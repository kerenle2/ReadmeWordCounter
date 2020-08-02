# ReadmeWordCounter
## Overview
    
    This project takes a list of git repositories as input, extract the readme file out of each repo and outputs a frequency count on each word of all the readme’s combined.
    It uses Apache beam pipline.
## How To Use
#### 1. clone this repository:
    git clone https://github.com/kerenle2/ReadmeWordCounter.git
#### 2. Go into the repository
    cd ReadmeWordCounter
#### 3. install dependencies:
    pip install -r requirements.txt
#### 4. run the app:
    python pipeline.py --input <list of repositories separted by comma>
    
    example:
    python pipeline.py --input octocat/hello-world,kerenle2/ReadmeWordCounter
    
#### 5. check the output file in "archive" dir and the logs in "logs" dir.
    
