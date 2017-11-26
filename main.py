from itertools import product

###############################################################################
# class for storing (attribute, value) pairs and the (decision, concept) pair #
###############################################################################
class entry():
    def __init__(self, attribute_values,attributes, decision_value, decision):
        self.A = {}
        for i, Attr in enumerate(attributes):
            self.A[Attr] = attribute_values[i]
        self.A[decision] = decision_value

################################################
# make the file into (a,v) and (d,v) pairs #
################################################
def parsefile(file):
    current_line = 0
    got_attributes = 0 # 0=haven't started reading, 1=in progress, 2=done
    attributes = []
    attribute_values = []
    i = 0
    decision = ""
    decision_value = ""
    entries = {}
    for line in file:
        current_line += 1
        line = line.split()
        if line == []: # empty line
            continue
        elif (line[0] == "<") or (line[0] == "!"): # comment or first line
            continue
        elif line[0] == '[': # start of attribute list
            if line[-1] == ']': # attribute list also ends on this line
                attributes = line[1:-2]
                decision = line[-2]
                got_attributes = 2
                attr_values_to_gather = len(attributes)
            else: # attribute list doesn't end on this line
                got_attributes = 1
                attributes += line[1:len(line)]
        else:
            if got_attributes == 1: # reading attributes still
                if line[-1] == ']': # attribute list ends on this line
                    attributes += line[0:-2]
                    decision = line[-2]
                    got_attributes = 2
                    attr_values_to_gather = len(attributes)
                else: # attribute list doesn't end on this line
                    attributes += line#[0:-1]
            elif got_attributes == 2: # done reading attributes, so start reading values of each attribute
                if len(line)+len(attribute_values) <= len(attributes): #If the values are present on 2 lines
                    attribute_values += line
                elif len(line)-1 + len(attribute_values) == len(attributes):
                    attribute_values += [val for val in line[0:-1]]
                    decision_value = line[-1]
                    entries[i] = entry(attribute_values, attributes, decision_value, decision)
                    attribute_values = []
                    i += 1
                else:
                    print("\n\nerror: Problem reading line #" + str(current_line))
                    quit()

    return (entries,attributes,decision)

##########################################################################
# Find cut points #
###########################################################################
def find_cutpoints(entries, attributes):
    list_of_values = [[] for _ in range(len(attributes))]
    cut_points = [[] for _ in range(len(attributes))]
    for i, attr in enumerate(attributes):
        try:
            float(entries[0].A[attr])
            for case in entries:
                if (not(float(entries[case].A[attr]) in list_of_values[i])):
                    list_of_values[i].append(float(entries[case].A[attr]))
            list_of_values[i].sort()
        except:
            pass
        for k in range(len(list_of_values[i])-1):
            cut_points[i].append((float(list_of_values[i][k])+float(list_of_values[i][k+1]))/2.0)
        cut_points[i] = list(set(map(lambda x: float("{0:.2f}".format(x)), cut_points[i])))

    return cut_points, list_of_values

#######################################################################
# Create a new file with all cut points strategy
#######################################################################
def create_file_with_cutpoints(entries, attributes, decision, cut_points, list_of_values, datafilename = 'cutpointsfile.d'):
    datafile = open(datafilename, 'w')
    datafile.write("[ ")
    for index, attr in enumerate(attributes):
        if(cut_points[index] != []):
            for i in range(len(cut_points[index])):
                datafile.write(''.join([attr, "_", str(cut_points[index][i]), "\t"]))
        else:
            datafile.write(''.join([attr, " "]))
    datafile.write(''.join([decision, " ]\n"]))
    for i in entries:
        for index, attr in enumerate(attributes):
            if(cut_points[index] != []):
                for k in range(len(cut_points[index])):
                    if(float(entries[i].A[attr]) < cut_points[index][k]):
                        datafile.write(''.join([str(min(list_of_values[index])), ".." , str(cut_points[index][k]), "\t"]))
                    else:
                        datafile.write(''.join([str(cut_points[index][k]), ".." , str(max(list_of_values[index])), "\t"]))
            else:
                datafile.write(''.join([entries[i].A[attr], "\t"]))
        datafile.write(''.join([entries[i].A[decision],"\n"]))
    datafile.close()
    return datafilename

###########################################################################
# Checking if the dataset is consistent #
###########################################################################

def isconsistent(entries,attributes, partition_decision, single_partition, multipart_v):
    try:
        multipart = multipart_v[','.join(attributes[:])]
    except:

        multipart = partitionAttribute(entries, attributes[-1])
        for i, attr in reversed(list(enumerate(attributes))):
            try:
                multipart = multipart_v[','.join(attributes[i:])]
            except:
                multipart = partitionAttributes(single_partition[attr], multipart)
                multipart_v[','.join(attributes[i:])] = multipart

    for entryM in multipart:
        subset = False
        if any(set(entryM).issubset(set(entryD)) for entryD in partition_decision):
            subset = True
        else:
            return False, multipart, multipart_v

    return True, multipart, multipart_v


##################################################
# function to partition a set based on a single attribute or a decision#
##################################################
def partitionAttribute(entries, Att):
    partition = [[0]]
    attr_values = [entries[0].A[Att]]

    for i in entries:
        if not(entries[i].A[Att] in attr_values):
            partition.append([i])
            attr_values.append(entries[i].A[Att])

    for i, j in product(range(len(entries)), range(len(partition))):
        if not(i in partition[j]) and (entries[i].A[Att] == attr_values[j]):
                partition[j].append(i)

    return partition

####################################################################
# function to compute the partition of several attributes together #
####################################################################
def partitionAttributes(part1,part2):
    part = []
    for elmnt1, elmnt2 in product(part1, part2):
        temp = list(set(elmnt1) & set(elmnt2))
        if not(temp == []):
            part.append(temp)
    return part

###########################################################################
# function to compute lower approximation of a dataset#
############################################################################

def to_lower(entries, attributes, decision, multipart, filename, cons_flag_l):
    set_of_concepts = [entries[0].A[decision]]
    for i in entries:
        if not(entries[i].A[decision] in set_of_concepts):
            set_of_concepts.append(entries[i].A[decision])

    if(len(set_of_concepts) < 3 and cons_flag_l == True):
        partition_c = {}
        for i in attributes:
            partition_c[i] = partitionAttribute(entries, i)
        for m in set_of_concepts:
            attribute_indices_l = LEM1(entries, attributes, decision, partition_c, multipart_c)
            rules_file_l = induce_certain_rules(entries, attributes, attribute_indices_l, decision, m, "my-data.certain.r")
    else:

        for m in set_of_concepts:
            lowerfile = open(filename, 'w+')
            lowerfile.write("[ ")

            for attr in attributes:
                lowerfile.write(''.join([attr, "  "]))
            lowerfile.write(''.join([decision, " ]\n"]))

            for j in multipart:
                if(len(j)==1):
                    lowerfile.write('\t'.join([entries[j[0]].A[i] for i in attributes]))
                    if(entries[j[0]].A[decision] == m):
                        lowerfile.write(''.join(["\t", m , " \n"]))
                    else:
                        lowerfile.write(''.join(["\tSPECIAL\n"]))
                else:
                    if (all(entries[k].A[decision] == m for k in j)):
                        for k in j:
                            lowerfile.write('\t'.join([entries[k].A[i] for i in  attributes]))
                            lowerfile.write(''.join(["\t", m , " \n"]))
                    else:
                        for k in j:
                            lowerfile.write('\t'.join([entries[k].A[i] for i in attributes]))
                            lowerfile.write(''.join(["\tSPECIAL\n"]))

            lowerfile.seek(0)
            entries_l, attributes_l, decision_l = parsefile(lowerfile)
            partition_l = {}
            for i in attributes_l:
                partition_l[i] = partitionAttribute(entries_l, i)

            attribute_indices_l = LEM1(entries_l, attributes_l, decision_l, partition_l)
            print("After LEM1 for lower file, the attribute_indices = ", attribute_indices_l)
            rules_file_l = induce_certain_rules(entries_l, attributes_l, attribute_indices_l,decision_l, m, "my-data.certain.r")
            lowerfile.close()
        print("********************************************************")

###########################################################################
# function to compute Upper approximation of  a dataset #
############################################################################

def to_upper(entries, attributes, decision, multipart, filename):
    set_of_concepts = [entries[0].A[decision]]
    for i in entries:
        if not(entries[i].A[decision] in set_of_concepts):
            set_of_concepts.append(entries[i].A[decision])

    for m in set_of_concepts:
        upperfile = open(filename, 'w+')
        upperfile.write("[ ")

        for attr in attributes:
            upperfile.write(''.join([attr, "  "]))
        upperfile.write(''.join([decision, " ]\n"]))

        for j in multipart:
            if(len(j)==1):
                upperfile.write('\t'.join([entries[j[0]].A[i] for i in attributes]))
                if(entries[j[0]].A[decision] == m):
                    upperfile.write(''.join(["\t", m , " \n"]))
                else:
                    upperfile.write(''.join(["\tSPECIAL\n"]))
            else:
                if (any(entries[k].A[decision] == m for k in j)):
                    for k in j:
                        upperfile.write('\t'.join([entries[k].A[i] for i in  attributes]))
                        upperfile.write(''.join(["\t", m, " \n"]))
                else:
                    for k in j:
                        upperfile.write('\t'.join([entries[k].A[i] for i in attributes]))
                        upperfile.write(''.join(["\tSPECIAL\n"]))

        upperfile.seek(0)
        entries_u, attributes_u, decision_u = parsefile(upperfile)

        partition_u = {}
        for i in attributes_u:
            partition_u[i] = partitionAttribute(entries_u, i)

        attribute_indices_u = LEM1(entries_u, attributes_u, decision_u, partition_u)

        rules_file_u = induce_certain_rules(entries_u, attributes_u, attribute_indices_u, decision_u, m, "my-data.possible.r")
        upperfile.close()
    print("********************************************************")

###########################################################
# Implementing LEM1
###########################################################
def LEM1(entries, attributes, decision, partition_s, multipart_lem = {}):
    partD = partitionAttribute(entries, decision)
    A = [i for i in attributes]
    P = list(A)
    count = 0
    partition_lem = []
    attribute_indices = []
    for i in A:
        Q = [j for j in P if j != i]
        if(len(Q) >= 1):
            cons_flag, multipart, multipart_lem = isconsistent(entries, Q, partD, partition_s, multipart_lem)
            if(cons_flag):
                P = list(Q)

    attribute_indices = list(P)
    return attribute_indices

###########################################################
# Implementing dropping conditions
###########################################################
def dropping_conditions(entries, attribute_indices, case_number, decision_value):
    A = [i for i in attribute_indices]
    cases_covered = []
    P = list(A)
    flag = False
    new_attribute_indices = []
    for h, k in enumerate(A):
        cases = []
        Q = [j for j in P if j != k]
        new_attribute_values = [entries[case_number].A[s] for s in Q]
        for i in entries:
            entry_values = [entries[i].A[attr] for attr in Q]
            if ((new_attribute_values == entry_values) and (entries[i].A[decision] == decision_value)):
                flag = True
                cases.append(i)
                continue
            elif ((new_attribute_values == entry_values) and (entries[i].A[decision] != decision_value)):
                flag = False
                break
            else:
                continue
        if(flag == True):
            cases_covered.extend(cases)
            P = list(Q)

    new_attribute_indices = list(P)
    return new_attribute_indices, cases_covered

#####################################################################################
# write induced rules  to a file #
######################################################################################
def induce_certain_rules(entries,attributes, attribute_indices, decision, decision_value, datafilename):
    datafile = open(datafilename, 'a')
    cases_covered = []
    testing_rules = {}
    multipart = partitionAttribute(entries, attribute_indices[0])
    for i in attribute_indices:
        part = partitionAttribute(entries,i)
        multipart = partitionAttributes(part,multipart)
    for j in multipart:
        cases_covered_l = []
        if(entries[j[0]].A[decision] == decision_value and j[0] not in set(cases_covered)):
            attributes_list, cases_covered_l = dropping_conditions(entries, attribute_indices, j[0], decision_value)
            cases_covered.extend(cases_covered_l)
            j.extend(cases_covered_l)
            testing_rules[tuple(j)] = attributes_list

    for key in testing_rules:
        if any(set(key).issubset(set(i)) for i in testing_rules if i != key):
            continue
        else:
            j = list(set(key))
            for attr in testing_rules[key][0:-1]:
                datafile.write(''.join(["(" , attr , ", " , str(entries[j[0]].A[attr]),
                                        ")" , " & "]))
            last_attr = testing_rules[key][-1]
            datafile.write(''.join(["(", last_attr ,", " , str(entries[j[0]].A[last_attr]),
                            ") ->  (" , decision , ", " , str(entries[j[0]].A[decision]) , ")\n"]))
    datafile.close()
    return datafile

##########################################################
# The program starts here #
#########################################################
multipart_c = {}
filename = input("Enter the name of the input file >")
while(True):
    if filename.endswith(".d"):
        try:
            input_file = open(filename,"r") #opens the given input file if exists
            break
        except:
            filename = input("The file doesn't exist. Please re-enter the correct name >")
    else:
        filename = input("You should enter a .d file >")

print("\nOk. Reading file...")
(entries_o,attributes,decision) = parsefile(input_file)
input_file.close()
print("Done parsing file")
print("Number of cases = ", len(entries_o))
print("Attributes = ", attributes)
print("Decision = ", decision)

print("Finding cutpoints.....")
cut_points, list_of_values = find_cutpoints(entries_o, attributes)

print("Found the cut points. Now creating a file with cutpoints....")
new_file = create_file_with_cutpoints(entries_o, attributes, decision, cut_points, list_of_values)
new_file = open(new_file, "r")
(entries_c, attributes_c, decision_c) = parsefile(new_file)

partition_d = partitionAttribute(entries_c, decision_c)
part_single = {}
for i in attributes_c:
    part_single[i] = partitionAttribute(entries_c, i)

print("Checking for Consistency...")
consistent_flag, attributes_partition, multipart_c = isconsistent(entries_c, attributes_c, partition_d, part_single, multipart_c)
if(consistent_flag):
    print("Table after finding cut points is consistent")
    to_lower(entries_c, attributes_c, decision_c, attributes_partition,"lower.d", consistent_flag)
    datafile = open("my-data.possible.r", 'w')
    datafile.write("! Possible ruleset is not shown since it is identical with the certain rule set. ")
    datafile.close()
else:
    print("The provided table after finding cutpoints is not consistent\n"
           "so we will find lower and upper approximations")
    to_lower(entries_c, attributes_c, decision_c, attributes_partition,"lower.d", consistent_flag)
    to_upper(entries_c, attributes_c, decision_c, attributes_partition,"upper.d")

print("Files are Created with rules...")
