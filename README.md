# Reliable Data Transfer Protocol in Python

Implementation of RDT layer based on Python's built-in UDP libarary.

University of Hong Kong CS COMP3234 Personal Project.

Test code is not written by me. My goal was to complete the rdt4.py

<br>

## Implementation Details

<table>
    <thead>
        <tr>
            <th colspan="4">Header</th>
            <th>Payload</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Type</td>
            <td>Seq #</td>
            <td>Checksum</td>
            <td>Payload Length</td>
            <td>Payload</td>
        </tr>
        <tr>
            <td>1 Byte</td>
            <td>1 Byte</td>
            <td>2 Byte</td>
            <td>2 Byte</td>
            <td>1000 Byte</td>
        </tr>
        <tr>
            <td>ACK=11 Data=12</td>
            <td>0 or 1</td>
        </tr>
    </tbody>
</table>


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
