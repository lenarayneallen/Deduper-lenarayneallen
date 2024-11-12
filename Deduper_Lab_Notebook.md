# Deduper Lab Notebook

# October 13th, 2024

- made new environment (on my machine) for deduper called `deduper`
- installed samtools: `mamba install samtools -c bioconda`
- going to do most of the testing of my code on my machine and switch to Talapas when I start running it with the big filesN

# October 16th, 2024

- wrote psuedocode in a markdown:
    - `/Users/lenaallen/bioinfo/Bi624/Deduper-lenarayneallen/Deduper_Psuedocode.md`
    - pushed to github
- test files:
    - `input_testfile.sam`
    - `output_testfile.sam`
    - pushed to top level directory on github

# November 2nd-5th, 2024

- started writing actual script!!!
- wrote deduper V1, V2, and V3. At V3 (`/Users/lenaallen/bioinfo/Bi624/Deduper-lenarayneallen/old_scripts/deduper_V3.py` on my machine), scp’d to talapas to start working with big files and continue editing there

# November 10th, 2024

- Added argparse to script, including options -f (input file), -u (umi file), -o (output file)
- Initially ran within a shell script `/projects/bgmp/lenara/bioinfo/Bi624/deduper/deduper.sh`
- Had trouble getting it to run just on command line
    - Update: Forgot my shebang inside python script. I may be stupid.

# November 11th, 2024

- Figured out and added argparse help message
- sorted **`/projects/bgmp/shared/deduper/C1_SE_uniqAlign.sam` with samtools**
    - saved the sorted output as a gzipped sam file as to not take up too much space on talapas
        - `/projects/bgmp/lenara/bioinfo/Bi624/deduper/C1_SE_uniqAlign_sorted.sam.gz`
    - because of this, I temporarily edited my python code to read a gzipped file, and removed this after running **`C1_SE_uniqAlign.sam`** to get the counts needed for the survey part of the assignment
    - output: `/projects/bgmp/lenara/bioinfo/Bi624/deduper/C1_SE_uniqAlign_deduped.sam`
- renamed script `allen_deduper.py`
    - on talapas: `/projects/bgmp/lenara/bioinfo/Bi624/deduper/allen_deduper.py`
    - scp’d to my machine and pushed to github