#!/usr/bin/env python
import re
import argparse

def get_args():
    parser = argparse.ArgumentParser(add_help=True,
                                     epilog="Script to remove duplicated reads (PCR duplicates) from a SAM file. Input SAM file must be already sorted using samtools. If duplicates are present, the first read encountered is written to the output file specified using -o. User must also provide an input file of Unique Molecular Identifiers (UMIs) using -u.")
    parser.add_argument("-o", "--outfile", help="Absolute file path to output sorted sam file", required = True, type=str)
    parser.add_argument("-u", "--umi", help="File containing the list of UMIs", required=True,type=str)
    parser.add_argument("-f", "--f",help="Absolute file path to input sorted sam file", required=True,type=str)
    parser.print_help()
    return parser.parse_args()

def rev_comp(seq: str) -> str:
    '''Reverse complements a sequence'''
    basedict = {"A":"T", "T":"A", "C":"G", "G":"C"}
    baselist = []
    rev = seq[::-1]
    for i in rev:
        baselist.append(basedict[i])
    return ''.join(baselist)

def extract_SAM_info(samline: str) -> dict:
    '''Given an alignment line of a SAM file, extracts the 
    UMI, CHR, POS, CIGAR, and STRAND and returns them in the form of a dictionary.'''
    
    #split and strip line
    sline = samline.strip()
    sline = samline.split("\t")
    #extract chromosome
    chrom = sline[2]

    #extract umi from label
    label = sline[0]
    label = label.split(":")
    umi = label[-1]

    #extract position
    pos = int(sline[3])
    #extract cigar string
    cig = sline[5]
    #parse bitwise flag to determine strandedness
    bitwise = int(sline[1])
    if ((bitwise & 16) == 16):
        strd = "-"
    else:
        strd = "+"
    
    #format this information as a dictionary
    linedict = {"UMI":umi, "chromosome":chrom, "position":pos, "cigar":cig, "strand":strd}
    
    return linedict

def pos_adj(SAM_info: dict) -> dict:
    '''Extracts the position and cigar string from a dictionary of values generated by extract_SAM_info. 
    If soft clipping occurs, it returns the dictionary with the position adjusted for softclipping. 
    If it is a negative strand , it needs to look for soft clipping at the end of the cigar string and also account for deletions, Ms, and Ns. 
    If it is a positive strand, it needs to look for soft clipping at the beginning of the cigar string'''
    cigarstring = SAM_info["cigar"]

    #using regex to parse cigar string
    d = re.compile(r'\d+')
    l = re.compile(r'[A-Z]')

    #creates two lists: 
    #letters (holding the letters in the cigar string in order)
    #and numbers (holding the numbers in the cigar string in order)
    letters = l.findall(cigarstring)
    numbers = d.findall(cigarstring)

    #if positive strand
    if SAM_info["strand"] == '+' and letters[0] == "S":
        SAM_info["position"] = SAM_info["position"] - int(numbers[0])    
    #if not positive strand
    elif SAM_info["strand"] == '-':
        #tally number of Ms, Ds, Ns, and Ss in cigar string
        M = 0
        D = 0
        N = 0
        S = 0
        for i, character in enumerate(letters):
            if character == "M":
                M += int(numbers[i])
            if character == "D":
                D += int(numbers[i])
            if character == "N":
                N += int(numbers[i])
            #only consider soft clipping at the end of cigar string for negative strand
            if character == "S" and i == len(letters) - 1:
                S += int(numbers[i])
        #adjust position in original input dictionary
        SAM_info["position"] = M + D + S + N + SAM_info["position"] - 1
    return SAM_info


def filter_pcr_dupes(chrumi_dict: dict) -> tuple:
    '''Given a dictionary where keys = (umi, position, strand) and values = SAM file lines with the same UMI, chromosome, 
    and position (after adjustment), creates a list of lines with PCR duplicates filtered out, selecting the first entry of any duplicates. Also counts
    the number of UMIs enountered that are not in the provided list of UMIs. Returns a tuple of structure (deduplicated_list, # of incorrect UMIs)'''
    deduped = []
    wrongumis = 0
    for key in chrumi_dict:
        if key[0] in UMI_list:
            deduped.append(chrumi_dict[key][0])
        else:
            wrongumis += 1
            
    return (deduped, wrongumis)

args = get_args()
f = args.f
o = args.outfile
u = args.umi

#making UMI lists (forward and reverse comps)
rev_UMI_list = []
UMI_list = []
wrongumis_total = 0

with open(u, "r") as umi_file:
    for line in umi_file:
        line = line.strip()
        UMI_list.append(line)

for i in UMI_list:
    rev_UMI_list.append(rev_comp(i))


#open SAM file as sam and output file to be written to
with open(f, "rt") as sam, open(o, "w") as of:
    #initialize a dictionary where keys will equal (umi, position, strand) and values will equal a list of lines with the same umi, strand, and position.
    #This dictionary will be cleared and overwritten when current_chr changes
    chr_dict = {}
    firstchr = True
    current_chr = None
    #for each line in the sam file (which is already sorted by chr)
    for line in sam:
        #if line is a header line, write to output file
        if line.startswith("@") == True:
            of.write(line)
        #if line is not a header line
        elif line.startswith("@") == False:
            #if it is the first non-header line
            if firstchr == True:
                #extract necessary values from line
                lineinfo = extract_SAM_info(line)
                #set current_chr as the chromosome from the first line
                current_chr = lineinfo["chromosome"]
                lineumi = lineinfo["UMI"]
                #adjust position
                lineinfo = pos_adj(lineinfo)
                #add to dictionary
                chr_dict[(lineumi, lineinfo["position"], lineinfo["strand"])] = []
                chr_dict[(lineumi, lineinfo["position"], lineinfo["strand"])].append(line)
                firstchr = False
            
            #if it is not the first line
            if firstchr == False:
                #extract necessary values from line 
                lineinfo = extract_SAM_info(line)
                chromo = lineinfo["chromosome"]
                lineumi = lineinfo["UMI"]

                #if the chromosome has not changed
                if current_chr == chromo:
                    #adjust position
                    # print(lineinfo)
                    lineinfo = pos_adj(lineinfo)
                    # print(lineinfo)
                    #append to dictionary
                    if (lineumi, lineinfo["position"], lineinfo["strand"]) in chr_dict:
                        chr_dict[(lineumi, lineinfo["position"], lineinfo["strand"])].append(line)
                    else:
                        chr_dict[(lineumi, lineinfo["position"], lineinfo["strand"])] = []
                        chr_dict[(lineumi, lineinfo["position"], lineinfo["strand"])].append(line)

                #if chromosome HAS changed
                elif current_chr != chromo:
                    # print(chr_dict)
                    #filter out pcr duplicates
                    deduped = filter_pcr_dupes(chr_dict)
                    deduped_list = deduped[0]
                    wrongumis_total += deduped[1]
                    #print non-duplicate lines to output file
                    for l in deduped_list:
                        of.write(l)
                    
                    #update current chromosome and clear dictionary
                    current_chr = chromo
                    chr_dict.clear()
                    #append line info to newly-cleared dictionary
                    lineinfo = pos_adj(lineinfo)
                    chr_dict[(lineumi, lineinfo["position"], lineinfo["strand"])] = []
                    chr_dict[(lineumi, lineinfo["position"], lineinfo["strand"])].append(line)
    
    #if you reach the end of the file, filter out pcr duplicates
    deduped = filter_pcr_dupes(chr_dict)
    deduped_list = deduped[0]
    wrongumis_total += deduped[1]

    #print total number of wrong umis 
    print(f"Total wrong UMIs encountered: {wrongumis_total}")

    #write non-duplicates to output file
    for line in deduped_list:
        of.write(line)


