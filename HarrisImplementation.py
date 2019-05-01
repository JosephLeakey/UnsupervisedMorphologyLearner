import time

class HarrisNode:
    def __init__(self, character):
        self.character = character
        self.successors = []
        # Initialise node with a character and an empty successor set

    @classmethod
    def start(HarrisNode):
        return HarrisNode("START")
        # Initialises a starting node

    def appendstring(self, word):
        if self.character == "#":
            return

        character = word.lower()[0]

        if character not in self.children():
            self.successors.append(HarrisNode(character))
        
        if len(word) > 1:
            self.child(character).appendstring(word[1:])
        elif "#" not in self.child(character).children():
            self.child(character).successors.append(HarrisNode("#"))
        # Recursively appends the characters of an input string to the node (followed by the "#" symbol after the final character)

    def appendstrings(self, corpus):       
        if type(corpus) is str:
            corpus = corpus.split()
        
        for word in corpus:
            self.appendstring(word)
        # Automatically splits all of the words in a block of text and appends them to the node

    def factor(self):
        if self.children() == ["#"]:
            return 0
        else:
            return len(self.successors)
        # Returns the node's branching factor
        # Returns 0 if the character is *only* followed by an end-node

    def child(self, string):
        if (string[-1] == "#"):
            print("End-nodes cannot be returned")
            return None
        
        if len(string) > 1:
            return self.successors[self.childindex(string[0])].child(string.lower()[1:])
        else:
            return self.successors[self.childindex(string[0])]
        # Returns the child node object corresponding to the specified string
            
    def prune(self, character):
        subtrie = self.successors.pop(self.childindex(character))

        if "#" not in self.children():
            self.successors.append(HarrisNode("#"))
                
        return subtrie
        # Prunes (and returns) the child node corresponding to the specified character (and any children of that node)
        # The pruned node is replaced with an end-node if one is not already a child

    def children(self):
        return [repr(child) for child in self.successors]
        # Returns the textual representations of the node's children in the order by which they were appended

    def childindex(self, character):
        try:
            return [repr(child) for child in self.successors].index(character.lower())
        except:
            print("[" + character + "] is not a child of node [" + self.character + "]")
            return None
        # Returns the index of the child node corresponding to the supplied character

    def trie(self):
        childset = []

        for successor in self.successors:
            childset.append(successor.trie())

        if len(childset) > 0:
            return self.character, childset
        else:
            return self.character
        # Returns a representation of the entire subtrie following the node
        # If the node is a starting node, this will return the entire trie      

    def distribution(self, string):
        flat = []

        node = self

        while True:
            if node.character != "START":
                flat.append(node.factor())

            if len(string) == 0:
                break
            
            node = node.child(string[0])
            
            if node == None:
                break

            string = string[1:]
            
        return flat
        # Returns the successor quantity distribution from the node across the supplied suffix
        # If the node is a root, supply a whole word instead
        # Characters are returned with their branching factors in a "flat" format

    def finalbranch(self, string):
        distribution = self.distribution(string)[:-1]
        
        for i in range(len(distribution))[::-1]:
            if distribution[i] > 1:
                return i + 1
        # Returns the index of the final branch in the trie branch corresponding to the given substring

    def __repr__(self):
        return self.character

    def __str__(self):
        return self.character + " | " + str(self.children())

# ---------------------------------------------------------------------------------------------------- #

def Harris(corpus, ESM, frequencymatching):
    if type(corpus) is str:
        corpus = corpus.split()
    
    splits = {}

    root = HarrisNode.start()
    root.appendstrings(corpus)
    # Build a trie from the corpus

    print("*" + ("=" * 50) + "*\n")

    if ESM > 0:        
        indexes = {}
        suffixlog = {}

        for word in corpus:
            # If ESM is enabled, catalogue all unique suffixes following all words' last splits
            # Also record their natural occurrence counts
            suffix = word[root.finalbranch(word):]

            if frequencymatching and len(suffix) < ESM:
                continue

            if suffix not in suffixlog:
                suffixlog[suffix] = 1
            else:
                suffixlog[suffix] += 1

        if frequencymatching:
            suffixes = sorted(suffixlog, key=suffixlog.get)
        else:
            suffixes = sorted(suffixlog, key=len)
            
        suffixes.reverse()
        # Sort the suffix list to place greater precedence on more frequently-occuring suffixes

        print("EAGER SUFFIX MATCHES")
        
        for word in corpus:
            if len(word) <= 1:
                continue
            
            for suffix in suffixes:
                if word not in indexes and word.endswith(suffix):
                    # Match each word with the most commonly-occurring documented suffix that it ends with
                    split = word.rfind(suffix)

                    indexes[word] = split

                    print(word + " ← " + suffix + " [" + str(split) + "]")

                    break

        print()

    for word in corpus:
        if ESM > 0 and word in indexes and indexes[word] > 0:
            # If ESM is enabled, perform Harrisian analysis on the parts of each word *before* their newly-designated suffixes
            splits[word] = maxima(root.distribution(word[:indexes[word]]))
            splits[word].append(indexes[word])
        else:
            # Otherwise, perform standard Harrisian analysis
            splits[word] = maxima(root.distribution(word))

    print("SPLITS (ESM: " + str(ESM) + ")")

    for word in corpus:
        print(word + " " + str(splits[word]))

    print()

    return splits

def maxima(flat):        
    indexes = []

    i = 0

    rise = True

    for n in range(len(flat) - 1):            
        if flat[n] == flat[n + 1] and rise:
            i += 1
        else:
            if flat[n] > flat[n + 1] and rise:
                indexes.append(n + 1)

                if i > 0 and i < n:
                    indexes.append(n - i + 1)

                rise = False
            elif flat[n] < flat[n + 1]:
                rise = True
                    
            i = 0

    if i > 0 and i < len(flat) - 1:
        indexes.append(len(flat) - i)
        # If a part of a word is being evaluated (as opposed to a whole word), that substring's SQD may end with a plateau of maximal factors
        # If this happens, record only the starting position of the final plateau

    indexes.sort(key=int)

    return indexes
    # Determines local maxima in a flat distribution
    # Characters are returned with their branching factors and their positions

def harrissplit(root, string):
    return maxima(root.distribution(string))
    # Automatically calculates the successor quantity distribution for a word appended to the current node and returns the set of positions corresponding to that distribution's local maxima

def segment(word, splits):
    components = []

    components.append(word[:splits[0]])

    for i in range(len(splits) - 1):
        components.append(word[splits[i]:splits[i + 1]])

    components.append(word[splits[-1]:])

    return components
    # Segments a word based on a Harrisian distribution

# ---------------------------------------------------------------------------------------------------- #

corpus = "classic clean clear coma compete competing competitive compile compilation compute computing count counterproduction counterproductive countless court test tester trie tried"

# TEST SCRIPT
def testscript():
    root = HarrisNode.start()
    root.appendstrings(corpus)

    print(root)

    print(root.distribution("competitive"))
    # Sequence should be [2, 2, 2, 3, 1, 2, 2, 1, 1, 1, 0]
    print(root.finalbranch("competitive", False))
    # Should be "competi"
    print(root.finalbranch("competitive", True))
    # Should return 7

    root.appendstring("comatose")
    print(root.child("coma"))
    # Should return an "a" node with "#" and "t" as children
    print(root.child("comatose").children())
    # Should return ["#"]

    print(root.splits("competitive"))
    # Should return characters 4, 6 and 7

    root.child("competi").prune("t")
    print(root.child("competi"))
    # Should return an "i" node with "n" and "#" as children
    print(root.distribution("competing"))
    # Should return [2, 2, 2, 3, 1, 2, 2, 1, 0]
    print(root.splits("competing"))
    # Should return characters 4, 6 and 7

    ctrie = root.prune("c")
    ttrie = root.prune("t")
    #print(root.trie())
    #print(ctrie.trie())
    #print(ttrie.trie())

def testscript2():
    splits = Harris(corpus, False)

def testscript3():
    splits = Harris(corpus, True)

minESMlength = 1
ESMmatchsetting = True

def test(filename, outname):
    corpus = []
    
    with open("C:\\Users\\Joseph\\Desktop\\" + filename + ".txt", "r") as file:
        for line in file:
            word = line

            if "\n" in word:
                word = word[:word.rfind("\n")]

            if " " in word:
                word = word[:word.find(" ")]

            if len(word) > 0:
                corpus.append(word)

    timeA = time.process_time()

    splits = Harris(corpus, minESMlength, ESMmatchsetting)

    timeB = time.process_time()
    timeB = timeB - timeA

    with open("C:\\Users\\Joseph\\Desktop\\" + outname + ".txt", "w") as file:
        start = True
        
        for word in splits:
            out = word

            for index in splits[word]:
                out += " " + str(index)
            
            file.write(out + "\n")

        file.write(str(timeB))

        file.close()

def testutf(filename, outname):
    corpus = []
    
    with open("C:\\Users\\Joseph\\Desktop\\" + filename + ".txt", "r", encoding="utf8") as file:
        for line in file:
            word = line

            if "\n" in word:
                word = word[:word.rfind("\n")]

            if " " in word:
                word = word[:word.find(" ")]

            if len(word) > 0:
                corpus.append(word)

    timeA = time.process_time()

    splits = Harris(corpus, minESMlength, ESMmatchsetting)

    timeB = time.process_time()
    timeB = timeB - timeA

    with open("C:\\Users\\Joseph\\Desktop\\" + outname + ".txt", "w", encoding="utf8") as file:
        start = True
        
        for word in splits:
            out = word

            for index in splits[word]:
                out += " " + str(index)
            
            file.write(out + "\n")

        file.write(str(timeB))

        file.close()
    

# ---------------------------------------------------------------------------------------------------- #

#testscript2()
#testscript3()

#root = test("CornishCorpus100", "CornishCorpus100HarrisNoESM")
root = testutf("ScotsGaelicCorpus5028", "ScotsGaelicCorpus5028WithESMFreqMinLen1")
