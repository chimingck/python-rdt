# Reliable Data Transfer Protocal in Python

Implementation of RDT layer based on Python's built-in UDP libarary.

University of Hong Kong CS COMP3234 Personal Project.

Test code is not written by me. My goal was to complete the rdt4.py

<br>

## Implementation Details

| Header |   |   |   | Payload |
| ------ | - | - | - | ------- |
| Type | Seq # | Checksum | Payload Length | Payload |
| 1 Byte | 1 Byte | 2 Byte | 2 Byte | 1000 Byte |
| ACK=11 Data=12 | 0 or 1 |

Stop-and-Wait

Multi Window, Pipelined.

Go-Back-N and Selective Repeat NOT implemented

<br>

## Testing

First Put the transfer file in the project root directory.

Run the run-simulation3 program with corresponding params: \<filename\> \<drop rate\> \<error rate\> \<window size\>

For example on windows:
```
.\run-simulation3.bat pic.jpg 0.1 0.1 5
```

the pic.jpg will be transfered through local network and copied into ./Store folder