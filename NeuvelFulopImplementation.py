import ctypes
import time
import sys
import math
import random

ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)

class Relationship:
    def __init__(self, related, A, B, orientation):
        self.related = related
        self.A = A
        self.B = B
        self.orientation = orientation
        # Establishes a "relationship", which is defined here as a pair of stems/suffixes and a set of substrings that append onto them to produce corpus words
        # The "orientation" variable defines whether [A] and [B] are stems or suffixes
        # ORIENTATION: TRUE | [A] and [B] are stems; [related] is comprised of word endings
        # ORIENTATION: FALSE | [A] and [B] are suffixes: [related] is comprised of word beginnings

    def binds(self):
        return [self.A, self.B]
        # Returns the two stems or suffixes commonly connected to the related substrings

    def rule(self):
        string = ""
        
        if self.orientation:
            for i in range(len(max(self.related, key=len))):
                characters = [ending[i] for ending in self.related if len(ending) > i]

                if len(characters) < len(self.related):
                    string += "*"
                elif characters.count(characters[0]) == len(characters):
                    string += characters[0]
                else:
                    string += "#"

            return (self.A + string, self.B + string)
        else:
            for i in range(len(max(self.related, key=len))):
                characters = [stem[-(i + 1)] for stem in self.related  if len(stem) > i]

                if len(characters) < len(self.related):
                    string = "*" + string
                elif characters.count(characters[0]) == len(characters):
                    string = characters[0] + string
                else:
                    string = "#" + string

            return (string + self.A, string + self.B)
        # Returns the rule expressing the stem/suffix relationship that ties together all strings in the "related" set (in the format defined by Neuvel and Fulop)
        # This is expressed as pair of "rule strings" containing characters, hash symbols and star symbols
        # Characters in the relationship's two stems/suffixes and (separately) across related substrings will appear naturally in rule strings
        # Hash (#) characters denote character positions that must be filled by strings formed from the relationship
        # Conversely, star (*) characters denote positions that *may* (or may not) be filled
        # EXAMPLE: "*##ceive <> *##ception" denotes that all strings in the relationship must either:
            # - End with "ceive" and be 7 or 8 characters long
            # - End with "ception" and be 9 or 10 characters long
        # Rules of this format can be used to produce new strings from other strings

    def __str__(self):
        if len(self.A) == 0:
            reprA = "#"
        else:
            reprA = self.A

        if len(self.B) == 0:
            reprB = "#"
        else:
            reprB = self.B
        
        if self.orientation:
            return "Stem A: " + reprA + "-\nStem B: " + reprB + "-\nEndings: " + str(self.related)
        else:
            return "Ending A: -" + reprA + "\nEnding B: -" + reprB + "\nStems: " + str(self.related)
        # Returns a string representation of the relationship, distinguishing the two stems/suffixes from the related substrings that they tie together

# Identifies and returns the analogous relationships tying strings together from across a corpus
# "Relationships" (as used in this context) are defined above
# CORPUS: The set of words to be examined
# MINMATCH: The number of words that each half of a (candidate) split must individually start off or end
# MATCHREQ: Stems and endings are only catalogued once their combined occurrence counts exceed this number
# RELREQ: A relationship (bound by two stems/suffixes) must tie at least this many substrings together to be returned
def relationships(corpus, minmatch, cachereq, relreq):
    if type(corpus) is str:
        corpus = corpus.split()

    if minmatch < 1:
        minmatch = 1

    if cachereq < minmatch:
        cachereq = minmatch

    if relreq < 1:
        relreq = 1
    # Set default parameters for the method if they're too low

    corpus = [word.lower() for word in corpus]
    # Normalise all the words in the corpus

    stems = []
    endings = []

    stemcache = [""]
    endingcache = [""]
    # These caches are maintained to accelerate component searches
    # If a stem or ending is in a cache, that means the component's occurrence count exceeds cachereq (which itself is equal to or more than minmatch)
    # It does *not*, however, mean that the component is a stem or an ending
    # A stem in the stemcache (or an ending in the endingcache) will only be taken as a stem (or an ending) if the occurrence count of the counterpart in a word containing it exceeds minmatch

    c = 0

    for word in corpus:        
        splits = []
        
        for i in range(len(word) + 1):
            # Go through each position of each word (including the positions before and after their ends) and calculate the respective occurrence quanities for the substrings before and after those positions (across the corpus)
            # If a split's total multiplicity is high enough, the resultant stem and ending will be recorded
            stemmultiplicity = 0
            endmultiplicity = 0

            stem = word[:i]
            end = word[i:]
                
            for key in corpus:
                if key != word:
                    if stem not in stemcache and key.startswith(stem):
                        stemmultiplicity += 1

                        if stemmultiplicity >= cachereq:
                            stemcache.append(stem)
                    elif end not in endingcache and key.endswith(end):
                        endmultiplicity += 1

                        if endmultiplicity >= cachereq:
                            endingcache.append(end)
                    else:
                        continue

                    if (stem in stemcache or stemmultiplicity >= minmatch) and (end in endingcache or endmultiplicity >= minmatch):
                        splits.append(i + 1)
                        break

        for split in splits:
            if word[:split] not in stems:
                stems.append(word[:split])

            if word[split:] not in endings:
                endings.append(word[split:])

        c += 1

        sys.stdout.write("\033[F")

        print(str(c) + " word(s) checked")

    print(str(len(stems)) + " stems | " + str(len(endings)) + " endings\n\n")
     
    relationships = []

    stemsearch = stems[:]
    endingsearch = endings[:]

    nck = int(math.factorial(len(stems)) / (2 * math.factorial(len(stems) - 2)))

    c = 0

    # For each pair of distinct registered stems, compile all of the endings that can be matched to both stems
    # If enough endings can be matched to a pair of stems, register the relationship between the stems and the endings
    for A in stems:
        stemsearch.remove(A)
        
        for B in stemsearch:            
            if len(A) == 0 or len(B) == 0 or A[-1] != B[-1]:                    
                related = []
                            
                for end in endings:
                    if str(A + end) in corpus and str(B + end) in corpus:
                        related.append(end)

                if related != [""] and len(related) >= relreq:
                    relationships.append(Relationship(related, A, B, True))

            c += 1

            sys.stdout.write("\033[F")

            print(str(c) + "/" + str(nck) + " stem combinations evaluated")

    n = len(relationships)

    print(str(n) + " stem relationships (with " + str(relreq) + " or more endings) found\n\n")

    nck = int(math.factorial(len(endings)) / (2 * math.factorial(len(endings) - 2)))

    c = 0

    # Do the same as above, except with pairs of distinct registered endings and sets of matching stems
    for A in endings:
        endingsearch.remove(A)
        
        for B in endingsearch:
            if len(A) == 0 or len(B) == 0 or A[0] != B[0]:
                related = []
                            
                for stem in stems:
                    if str(stem + A) in corpus and str(stem + B) in corpus:
                        related.append(stem)

                if related != [""] and len(related) >= relreq:
                    relationships.append(Relationship(related, A, B, False))

            c += 1

            sys.stdout.write("\033[F")

            print(str(c) + "/" + str(nck) + " ending combinations evaluated")

    n = len(relationships) - n

    print(str(n) + " ending relationships (with " + str(relreq) + " or more stems) found\n")

    # Return all of the relationships that link [relreq] words together
    return relationships

# Applies a rule to a word to produce that word's counterpart
# WORD: The word to be altered
# RULE: The rule to apply (expressed as a tuple of two strings containing letters, hashes and stars)
def applyrule(word, rule):
    match = None
    
    for half in rule:
        if len(word) > len(half) or len(word) < (len(half) - half.count("*")):
            continue
        # If the provided word is too short or too long to be matched with this half of the rule, move on
        
        offset = -1

        pattern = []

        for i in range(len(half)):
            if half[i] != "#" and half[i] != "*":
                if offset < 0:
                    offset = 0

                pattern.append([offset, half[i]])

            if offset >= 0:
                offset += 1
        # Compile the distribution of definite characters in this half of the rule
        
        if len(pattern) > 0 and pattern[0][1] not in word:
            continue

        # For each character in the provided word matching the first character of the definite pattern recorded from this half of the rule, attempt to match the pattern with the string
        # If a match is found, verify the string's other contents
        if len(pattern) == 0:
            halfstart = half[:half.find("#")]
            halfend = half[half.rfind("#") + 1:]
            
            if half[0] == "#":
                match = word[:half.count("#")]
            elif half[-1] == "#":
                match = word[-half.count("#"):]

            wordstart = word[:word.find(match)]
            wordend = word[word.find(match) + len(match):]
        else:
            for base in [index for index, character in enumerate(word) if character == pattern[0][1]]:
                matching = True
                
                for i in range(len(pattern) - 1):
                    if base + pattern[i + 1][0] >= len(word) or word[base + pattern[i + 1][0]] != pattern[i + 1][1]:
                        matching = False
                        
                        break

                if not matching:
                    continue

                halfstart = half[:half.find(pattern[0][1])]
                halfend = half[half.find(pattern[0][1]) + pattern[-1][0] + 1:]
                # Record the elements of the matching rule before and after the definite pattern's section

                match = word[base:base + pattern[-1][0] + 1]
                # Record the substring in the word that matches up with the definite pattern's section

                wordstart = word[:base]
                wordend = word[base + pattern[-1][0] + 1:]
                # Record the substrings in the word before and after the matching section
                
                if len(wordstart) > len(halfstart) or len(wordstart) < (len(halfstart) - halfstart.count("*")) or len(wordend) > len(halfend) or len(wordend) < (len(halfend) - halfend.count("*")):
                    match = None

                    continue
                
                break

        checked = half

        break

    if match is not None:
        # Get the other half of the rule and retrieve that half's unique contents (with respect to the matched half)
        for half in rule:
            if half != checked:
                frame = half

        frame = frame.replace(halfstart, wordstart, 1)
        frame = frame.replace(halfend, wordend, 1)

        out = ""

        for i in range(len(frame)):
            if frame[i] == "#" or frame[i] == "*":
                out += word[i]
            else:
                out += frame[i]

        print(word + " → " + wordstart + "[" + match + "]" + wordend + " → " + out + " | " + str(rule))
        return out
        # Return the transformation of the original string, as defined by the differences between the two halves of the supplied rule

    return None

# ---------------------------------------------------------------------------------------------------- #

#corpus = "receive reception conceive conception deceive deception honor honorem orator oratorem bake baked charge charged"
#corpus2 = "honor honorem orator oratorem"
#corpus3 = "bake baked charge charged"

#test = relationships(corpus, 1, 2, 3)
#for rel in test:
#    print(rel)
#    print(rel.rule())

#applyrule("enception", ("*##ceive", "*##ception"))

def test(filename, outname):
    for x in range(1):
        complement = []

        print("Loading words...")
        
        with open("C:\\Users\\Joseph\\Desktop\\" + filename + ".txt", "r") as file:
            for line in file:
                word = line

                if "\n" in word:
                    word = word[:word.rfind("\n")]

                if " " in word:
                    word = word[:word.find(" ")]

                if word not in complement:
                    complement.append(word)

                #print(word)

        minicorpus = []

        while len(minicorpus) < 1000:
            word = complement.pop(random.randrange(len(complement)))

            minicorpus.append(word)

        timeA = time.process_time()

        outset = []

        relset = relationships(minicorpus, 1, 2, 3)

        for rel in relset:        
            for word in minicorpus:
                out = applyrule(word, rel.rule())

                if out != None and out not in minicorpus and out not in outset:
                    outset.append(out)

        timeB = time.process_time()
        timeB = timeB - timeA

        incomplement = 0

        if len(outset) == 0:
            genaccuracy = 0
        else:
            for word in outset:
                if word in complement:
                    incomplement += 1

            genaccuracy = float(incomplement / len(outset))

        with open("C:\\Users\\Joseph\\Desktop\\" + outname + "Run" + str(x + 1) + ".txt", "w") as file:
            for word in outset:
                file.write(word + "\n")

            file.write("TIME: " + str(timeB) + "\n")
            file.write("TOTALCOUNT: " + str(len(outset)) + "\n")
            file.write("IN COMPLEMENT COUNT: " + str(incomplement) + "\n")
            file.write("GENACCURACY: " + str(genaccuracy) + "\n\n")

            for rel in relset:
                file.write(str(rel.rule()) + "\n")

            file.close()

    input("[ENTER]: Close")

def test2():
    corpus = "receive reception conceive conception deceive deception honor honorem orator oratorem bake baked charge charged petor"
    corpus = corpus.split()

    relset = relationships(corpus, 1, 2, 3)

    for rel in relset:
        for word in corpus:
            ech = applyrule(word, rel.rule())

test("CornishCorpus9645", "CornishCorpus1000NeuvelFulopMin1Cache2Req3")

#test2()
#applyrule("petor", ('*###or', '*###orem'))
