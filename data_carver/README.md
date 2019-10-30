# Data Carver
Python script to carve known file formats from a binary file

## Methodology
1. Read through input `--file`
2. Store the offset for every recognized file signature
3. Update offset data structure with EOFs as they are found
4. Ignore all files without a valid EOF trailer
5. Carve files

## Engineering goals
- Adding support for new file types should be easy
- Optimize signature lookup time, due to O(N) lookup operations

## Shortcomings
- File trailers are required
- Convoluted and non-intuitive data structures
- File signatures are hard-coded, and not read from config file
- No file verification, every potential file is carved

## Improvements without library restriction
- Import image library to verify if carved PNG/JPG files can be loaded

## Interesting discoveries
- High false-positive rate for JPG, due to short signature/trailer (low entropy)
- Very low false-positive rate on PNG/PDF, longer signatures
