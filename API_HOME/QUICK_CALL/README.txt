QUICK CALL: a one-off DeepSeek job in a folder you can copy.

  1. 0 NEW COPY.bat    makes a fresh copy of this folder next to it (asks for a name)
  2. prompt.txt        write what you want
  3. input\            drop in the files to read, grade, evaluate ... (or none: the prompt alone is sent)
  4. RUN.bat           one call per file, 30 at once; answers land in output\ one by one
     DRY_RUN.bat       shows what would be sent, sends nothing

Run it again and files that already have an answer are skipped (delete the answer, or RUN.bat --redo, to redo them).
Change the prompt and every file runs again, because answers are kept per prompt.
No other files needed: this folder works on its own, anywhere.
