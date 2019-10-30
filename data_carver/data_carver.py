#!/usr/bin/env python3
# forbidden imports: argparse
import os
from util import md5sum, parse_args


def get_offsets(args):
    ''' Return offsets for all potential files. Store every recognized file
        signature as found. Any files found without finding a valid EOF trailer
        are ignored.
    '''
    # TODO move these to a config file
    signatures = {
        b'\xFF': ('jpg', b'\xFF\xD8'),
        b'\x25': ('pdf', b'\x25\x50\x44\x46'),
        b'\x89': ('png', b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'),
    }
    trailers = {
        b'\xFF': ('jpg', b'\xFF\xD9'),
        b'\x25': ('pdf', b'\x25\x45\x4F\x46'),
        b'\x49': ('png', b'\x49\x45\x4e\x44\xae\x42\x60\x82'),
    }

    # store file offset tuples in the form (EOF is initialized to 0):
    # {
    #   'png': [(<SOF1>, <EOF1>),
    #   'jpg': [(<SOF2>, <EOF2>), (<SOF3>, <EOF3>)],
    # ...
    offsets = {}
    for filetype in signatures:
        offsets[signatures[filetype][0]] = []

    try:
        with open(args['file'], 'rb') as FILE:
            byte = FILE.read(1)
            while byte != b'':
                # check for file signature
                if byte in signatures:
                    # rewind 1 byte and store offset
                    FILE.seek(-1, 1)
                    offset = FILE.tell()

                    # retrieve full signature
                    sig = signatures[byte][1]

                    candidate = FILE.read(len(sig))

                    if candidate == sig:
                        if args['verbose']:
                            print("{} signature found at {}".format(signatures[byte][0], hex(offset)))
                        # add new file offset tuple
                        offsets[signatures[byte][0]].append((offset, 0))
                    else:
                        # recover file offset
                        FILE.seek(offset+1)

                # also check for file trailer (shared first byte between header and trailer)
                if byte in trailers:
                    # rewind 1 byte and store offset
                    FILE.seek(-1, 1)
                    offset = FILE.tell()

                    # retrieve full signature
                    tail = trailers[byte][1]

                    candidate = FILE.read(len(tail))

                    if candidate == tail:
                        if args['verbose']:
                            print("{} trailer found at {}".format(trailers[byte][0], hex(offset)))

                        # update EOF for all tuples of this filetype
                        for index, offset_tuple in enumerate(offsets[trailers[byte][0]]):
                            offsets[trailers[byte][0]][index] = (offset_tuple[0], offset+len(tail))


                    else:
                        # recover file offset
                        FILE.seek(offset+1)

                byte = FILE.read(1)

        # remove invalid tuples
        offsets = clean_offsets(offsets)

        return(offsets)

    except IOError:
        print("Could not open file: {}".format(args['file']))


def clean_offsets(offsets):
    '''remove all tupels where EOF is before SOF'''
    # create fresh structure
    cleaned = {}

    for filetype in offsets:
        cleaned[filetype] = []

        for offset_tuple in offsets[filetype]:
            if offset_tuple[0] < offset_tuple[1]:
                cleaned[filetype].append(offset_tuple)
    return cleaned


def carve(args, offsets):
    block_size = 4096
    hashes = "{}/hashes.txt".format(args['dump'])

    # truncate hashes file
    with open(hashes, 'w') as FILE:
        FILE.close()

    try:
        with open(args['file'], 'rb') as READ_FILE:

            # loop over every file tuple
            for filetype in offsets:
                for num, file_tuple in enumerate(offsets[filetype]):
                    READ_FILE.seek(file_tuple[0])
                    file_size = file_tuple[1] - file_tuple[0]
                    write_filename = "{}/{}.{}".format(args['dump'], num, filetype)

                    with open(write_filename, 'w+b') as WRITE_FILE:
                        bytes_read = 0

                        # carve file in blocks
                        while bytes_read <= (file_size - block_size):
                            block = READ_FILE.read(block_size)
                            WRITE_FILE.write(block)
                            bytes_read += block_size
                        WRITE_FILE.write(READ_FILE.read(file_size - bytes_read))

                    with open(hashes, 'a') as HASHES:
                        file_hash = md5sum(write_filename)
                        HASHES.write("{}  {}\n".format(file_hash, os.path.basename(write_filename)))





    except IOError:
        print("Could not open file: {}".format(args['file']))


def main():
    args = parse_args()

    # recover all potential files
    file_offsets = get_offsets(args)

    # carve and write all potential files
    carve(args, file_offsets)


if __name__ == '__main__':
    main()
