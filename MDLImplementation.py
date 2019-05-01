import ctypes
import sys
import time
import random
import numpy as np
from string import ascii_lowercase
from math import *

ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)

bestlist = []

class Individual:
    def __init__(self, corpus):
        if type(corpus) is dict:
            self.corpus = corpus
        else:   
            self.corpus = {}

            if type(corpus) is str:
                corpus = string.lower().split()
            
            for word in corpus:
                self.corpus[word.lower()] = random.randint(1, len(word))

        self.nmax = sum(len(word) for word in corpus)
        # Can either instantiate with a list of words (which will be assigned random split positions) or an existing mapping

    def list(self):
        return [[word, self.corpus[word]] for word in self.corpus]
        # Returns a list of each word-split pairing

    def listabsolute(self):
        return [[word, abs(self.corpus[word])] for word in self.corpus]
        # Returns a list of each word-split pairing
        # Negative splits (indicating locked boundaries) are converted to positive values

    def wordlist(self):
        return list(self.corpus.keys())
        # Returns an ordered list of the words in the mapping

    def splitlist(self):
        return list(self.corpus.values())
        # Returns an ordered list of the splits in the mapping

    def splitlistabsolute(self):
        return [abs(self.corpus[word]) for word in self.corpus]
        # Returns an ordered list of the splits in the mapping
        # Negative splits (indicating locked boundaries) are converted to positive values

    def boundary(self, word):
        return self.corpus[word.lower()]
        # Acts as an interface for the core mapping

    def boundaryabsolute(self, word):
        return abs(self.corpus[word.lower()])
        # Acts as an interface for the core mapping
        # Returns negative splits (indicating locked boundaries) as positive values
    
    def stem(self, word):
        return word[:abs(self.corpus[word])]
        # Returns a word's assigned stem

    def suffix(self, word):
        return word[abs(self.corpus[word]):]
        # Returns a word's assigned suffix

    def segmented(self, word):
        word = word.lower()
        
        return word[:abs(self.corpus[word])] + "|" + word[abs(self.corpus[word]):]
        # Returns a copy of the word with the word's assigned split indicated

    def set(self, word, n, shift):
        word = word.lower()

        if word not in self.corpus:
            print("'" + word + "' is not defined in the corpus")
            return

        if self.corpus[word] < 0:
            print("'" + word + "': Boundary has been locked at position [" + str(abs(self.corpus[word])) + "] and cannot be changed")
            return

        if (shift):
            if self.corpus[word] + n < 1:
                p = 1
            elif self.corpus[word] + n > len(word):
                p = len(word)
            else:
                p = self.corpus[word] + n
        else:
            if n < 1:
                p = 1
            elif n > len(word):
                p = len(word)
            else:
                p = n

        self.corpus[word] = p

        return word[:p] + "|" + word[p:]
        # Changes a word's boundary
        # The "shift" parameter imposes relative changes (as opposed to absolute changes) if it's set to be True

    def lock(self, word):
        word = word.lower()
        
        if word not in self.corpus:
            print("'" + word + "' is not defined in the corpus")
            return

        self.corpus[word] = -self.corpus[word]
        # Locks (or unlocks) a word's split position
        # Locking is indicated by negation

    def islocked(self, word):
        word = word.lower()
        
        if word not in self.corpus:
            print("'" + word + "' is not defined in the corpus")
            return

        return self.corpus[word] < 0
        # Returns True if a word's split position is locked, and False otherwise

    def stems(self):
        stems = []

        for word in self.corpus:
            stem = word[:abs(self.corpus[word])]
            
            if stem not in stems:
                stems.append(stem)

        return stems
        # Returns a list of the (unique) stems defined by the individual

    def suffixes(self):
        suffixes = []

        for word in self.corpus:
            suffix = word[abs(self.corpus[word]):]

            if suffix not in suffixes:
                suffixes.append(suffix)

        return suffixes
        # Returns a list of the (unique) suffixes defined by the individual

    def n(self):
        return sum(len(stem) for stem in self.stems()) + sum(len(suffix) for suffix in self.suffixes())
        # Returns the total character-count across the sets of unique stems and suffixes defined by the individual

    def nmax(self):
        return self.nmax
        # Returns the total character-count of the original corpus

    def fitnessabsolute(self):
        return self.nmax - (sum(len(stem) for stem in self.stems()) + sum(len(suffix) for suffix in self.suffixes()))
        # Returns a fitness value for the individual, defined as [nmax - n]
        # As the sizes of the unique stem/suffix sets decrease, this value increases

    def fitnessproportion(self):
        return 1 - ((sum(len(stem) for stem in self.stems()) + sum(len(suffix) for suffix in self.suffixes())) / self.nmax)
        # Returns a fitness value for the individual, defined as [1 - (n / nmax)]
        # As the proportion between the counts of unique stem/suffix characters and corpus characters decreases, this value approaches one
        # This is not used in any calculations but is provided for anyone who might want to use it

    def __str__(self):
        string = ""

        first = True

        for word in self.corpus:
            if first:
                first = False
            else:
                string += "\n"
            
            string += word[:abs(self.corpus[word])] + "|" + word[abs(self.corpus[word]):] + " [" + str(abs(self.corpus[word.lower()])) + "]"

            if self.corpus[word] < 0:
                string += " {Locked}"

        return string
        # Returns a list of all the words in the corpus with their assigned split positions marked and their locks identified

    def __repr__(self):
        return self.corpus

# ---------------------------------------------------------------------------------------------------- #

# This method carries out Kazakov's naive genetic process
# CORPUS: The list of words to be operated on
# POPCOUNT: The maximum number of individuals stored at any one time
# GENCOUNT: The number of generations to be evaluated
# MUTPROB: The probability of a word's split position being randomly shifted if entropic locking is disabled
# FITNESSTHRESHOLD: Once an individual with a higher fitness rating than this has been found, it will be returned straight away
    # Feature disabled when set to 0
# ENTROPYTHRESHOLD: Once a boundary's collective entropy is judged to be higher than this, it or any sufficiently-varying neighbours will be set and locked in place
    # Entropic locking is disabled when set to 0
def genetic(corpus, popcount, gencount, mutprob, tournamentsize, fitnessthreshold, entropythreshold, seek):
    if popcount < 1 or gencount < 1 or mutprob < 0 or mutprob > 1 or tournamentsize < 0 or fitnessthreshold < 0 or entropythreshold < 0:
        print("One or more of the provided arguments are invalid")
        return None

    population = [None] * popcount
    # Generate an empty set to define the population

    for i in range(len(population)):
        population[i] = Individual(corpus)

        print("Spawned initial individual " + str(i + 1))
    # Use the corpus to generate and store a set of random individuals

    stemcache = {}
    suffixcache = {}

    best = None
    bestfitness = 0

    for g in range(gencount + 1):
        if (g < gencount):
            print("\n*" + ("=" * 50) + "*\n\nGENERATION " + str(g + 1) + " | POPULATION EVALUATION\n\nFitnesses")
        else:
            print("\n*" + ("=" * 50) + "*\n\nFINAL GENERATION | POPULATION EVALUATION\n\nFitnesses")
        
        distribution = []

        for i in range(len(population)):
            fitness = population[i].fitnessabsolute()

            if fitness > bestfitness:
                best = population[i]
                bestfitness = fitness
            
            distribution.append(fitness)

            print("Ind. " + str(i + 1) + " ← " + str(fitness))

        bestlist.append(bestfitness)

        if g == gencount or (fitnessthreshold > 0 and bestfitness > fitnessthreshold):
            break
        
        print("\nCurrent Fitness Record: " + str(bestfitness))

        total = sum(distribution)
        # Record and total the fitnesses of all the individuals in the population

        print("\nReproduction Probabilities")

        for i in range(len(distribution)):
            proportion = float(distribution[i] / total)

            print("Ind. " + str(i + 1) + " ← " + str(proportion))

            distribution[i] = proportion
            # For each individual, calculate a reproduction probability value
            # This is defined as the proportion of an individual's fitness to the total fitness count

        new = [None] * popcount
        # Generate an empty set to define the next generation's population

        print("\n*" + ("=" * 50) + "*\n\nGENERATION " + str(g + 1) + " | CHILD BIRTH AND MUTATION")

        for i in range(popcount):
            if tournamentsize > 0:
                at = {}
                bt = {}
                
                while len(at) < tournamentsize:
                    n = random.randint(0, len(population) - 1)
                    
                    at[n] = distribution[n]

                while len(bt) < tournamentsize:
                    n = random.randint(0, len(population) - 1)
                    
                    bt[n] = distribution[n]

                ai = max(at, key=at.get) + 1
                bi = max(bt, key=bt.get) + 1

                a = population[ai - 1]
                b = population[bi - 1]
            else:
                parents = np.random.choice(population, 2, p=distribution).tolist()
                a = parents[0]
                b = parents[1]

                ai = population.index(a) + 1
                bi = population.index(b) + 1
            
            a = a.splitlist()
            b = b.splitlist()
            # Select two "parent" individuals from the current population, weighting choices based on their reproduction probabilities
            # Individuals may be picked twice if their reproduction probabilities are high

            childsplits = {}

            for j in range(len(corpus)):
                childsplits[corpus[j]] = random.choice([a[j], b[j]])
            # Create a "child" split mapping from the two parents, randomly mixing their contents together

            child = Individual(childsplits)
            # Convert the child mapping into an individual
       
            print("\nChild " + str(i + 1) + " ← (" + str(ai) + " × " + str(bi) + ")\nMutation in progress...\n")

            c = 0
            
            for word in child.corpus:
                sys.stdout.write("\033[F")

                c += 1
                
                if not child.islocked(word):
                    # For each word in the new child mapping, consider mutating it
                    if entropythreshold > 0 and collectiveentropycacheaccess(corpus, word, child.boundary(word), stemcache, suffixcache) > entropythreshold:
                        # If entropic locking is enabled and a word's collective entropy (defined around the bound split position) is high enough, attempt to lock it
                        # The collective entropies of the left- and right-hand splits will also be measured and a definitive split will be randomly chosen from any of the three that indicate sufficient variation                        
                        if seek:
                            shifts = [0]
                            
                            if collectiveentropycacheaccess(corpus, word, child.boundary(word) - 1, stemcache, suffixcache) > entropythreshold:
                                shifts.append(1)
                            if collectiveentropycacheaccess(corpus, word, child.boundary(word) + 1, stemcache, suffixcache) > entropythreshold:
                                shifts.append(2)

                            shift = random.choice(shifts)

                            if shift == 1:
                                child.set(word, -1, True)

                                print(str(c) + " word(s) mutated | L LOCK ")
                            elif shift == 2:
                                child.set(word, 1, True)

                                print(str(c) + " word(s) mutated | R LOCK ")
                            else:
                                print(str(c) + " word(s) mutated | C LOCK ")
                        else:
                            print(str(c) + " word(s) mutated | C LOCK ")

                        child.lock(word)
                        # Once a boundary has been found to indicate enough entropic variation, either it or a nearby sufficiently-varying boundary will be chosen and locked for that word                        
                        continue

                    # If a boundary's collective entropy was judged as being insufficient or entropic locking is disabled (represented by the "entropythreshold" parameter being set to 0), attempt to mutate it without locking it
                    # Random mutations of unlocked boundaries are certain when entropic locking is enabled (to promote the discovery of healthy candidates)
                    if random.uniform(0, 1) < mutprob:
                        if random.uniform(0, 1) < 0.5:
                            child.set(word, -1, True)

                            print(str(c) + " word(s) mutated | L SHIFT")
                        else:
                            child.set(word, 1, True)

                            print(str(c) + " word(s) mutated | R SHIFT")
                    else:
                        print(str(c) + " word(s) mutated | IGNORED")
                else:
                    print(str(c) + " word(s) mutated | LOCKED ")

            print("\nMutation finished")

            new[i] = child
            # Store the newly-produced child individual in the new population

            if i < popcount - 1:
                print("\n*" + ("-" * 50) + "*")

        population = new
        # Set the base population for the next generation

    print("\n*" + ("=" * 50) + "*\n\nBest Individual | Fitness = " + str(bestfitness) + "\n" + str(best) + "\n")

    return best
    # Once the process has terminated following enough generations, return the healthiest observed individual

def stementropy(corpus, stem):
    if len(stem) == 0:
        return 0

    if type(corpus) is str:
        corpus = string.lower().split()
    
    e = float(0)

    successors = []

    for word in corpus:
        if len(word) > len(stem) and word.lower().startswith(stem.lower()):
            successors.append(word[len(stem)].lower())
    
    for character in ascii_lowercase:
        if (successors.count(character) > 0):
            e -= (successors.count(character) / len(successors)) * log2(successors.count(character) / len(successors))

    return e
    # Calculates and returns the next-letter entropy of a given stem across the corpus

def suffixentropy(corpus, suffix):
    if len(suffix) == 0:
        return 0

    if type(corpus) is str:
        corpus = string.split()

    e = float(0)

    predecessors = []

    for word in corpus:
        if len(word) > len(suffix) and word.lower().endswith(suffix.lower()):
            predecessors.append(word[-len(suffix) - 1].lower())
    
    for character in ascii_lowercase:
        if (predecessors.count(character) > 0):
            e -= (predecessors.count(character) / len(predecessors)) * log2(predecessors.count(character) / len(predecessors))

    return e
    # Calculates and returns the last-letter entropy of a given suffix across the corpus

def collectiveentropy(corpus, word, index):
    if type(corpus) is str:
        corpus = string.lower().split()
    
    word = word.lower()

    return stementropy(corpus, word[:index]) + suffixentropy(corpus, word[index:])
    # Returns the sum of the next- and last-letter entropies around a boundary in a given word

def stementropycacheaccess(corpus, stem, stementropycache):
    if stem.lower() in stementropycache:
        return stementropycache[stem.lower()]
    else:
        e = stementropy(corpus, stem)

        stementropycache[stem.lower()] = e

        return e

def suffixentropycacheaccess(corpus, suffix, suffixentropycache):
    if suffix.lower() in suffixentropycache:
        return suffixentropycache[suffix.lower()]
    else:
        e = suffixentropy(corpus, suffix)

        suffixentropycache[suffix.lower()] = e

        return e

def collectiveentropycacheaccess(corpus, word, index, stemcache, suffixcache):
    return stementropycacheaccess(corpus, word[:index], stemcache) + suffixentropycacheaccess(corpus, word[index:], suffixcache)

# ---------------------------------------------------------------------------------------------------- #

def test(filename, outname):
    corpus = []

    print("Loading words...")
    
    with open("C:\\Users\\Joseph\\Desktop\\" + filename + ".txt", "r", encoding="utf") as file:
        for line in file:
            word = line

            if "\n" in word:
                word = word[:word.rfind("\n")]

            if " " in word:
                word = word[:word.find(" ")]

            if word not in corpus:
                corpus.append(word)

            print(word)

    timeA = time.process_time()

    best = genetic(corpus, 32, 100, 0.01, 8, 0, 0, True)

    timeB = time.process_time()
    timeB = timeB - timeA

    fitness = best.fitnessabsolute()

    with open("C:\\Users\\Joseph\\Desktop\\" + outname + ".txt", "w", encoding="utf") as file:
        for word in corpus:
            file.write(word + " " + str(best.boundaryabsolute(word)) + "\n")

        file.write("TIME: " + str(timeB) + "\n")
        file.write("FITNESS: " + str(fitness) + "\n")

        for i in range(len(bestlist)):
            file.write("GEN " + str(i + 1) + " BEST: " + str(bestlist[i]) + "\n")

        file.close()

def test2(outname):
    corpus = ["chanta", "chantai", "chantais", "chantait", "chanter"]
    
    timeA = time.process_time()

    best = genetic(corpus, 8, 20, 1, 3, 275000, 4, True)

    timeB = time.process_time()
    timeB = timeB - timeA

    fitness = best.fitnessabsolute()

    with open("C:\\Users\\Joseph\\Desktop\\" + outname + ".txt", "w") as file:
        for word in corpus:
            file.write(word + " " + str(best.boundaryabsolute(word)) + "\n")

        file.write("TIME: " + str(timeB) + "\n")
        file.write("FITNESS: " + str(fitness) + "\n")

        for i in range(len(bestlist)):
            file.write("GEN " + str(i + 1) + " BEST: " + str(bestlist[i]) + "\n")
            
        file.close()

test("ScotsGaelicCorpus5028", "ScotsGaelicCorpus5028Gen-32x100Prob001")
#test2("Ech")
