

FLOW FIELD IN SUPERSONIC INLET                              /inlet/readme.txt

The files for this program are in the directory inlet 
  readme.txt     general description
  inlet.f90      program source code
  blank.cmn      common block to be included in inlet.f90
  fig9.dat       a typical data set (from the document)
  fig9.out       the output from this data set


The reference documents for this program may be accessed
from the web page https://www.pdas.com/inletrefs.html The description
of the input to Inlet may be found in NASA TN D-2897.

To compile this program, use the command
   gfortran inlet.f90 -o inlet.exe


DESCRIPTION

This is a program that was used heavily during the development of the
US SST program in the late 1960s-1970s. It seems to have fallen out of
use, possibly because of the availability of truly 3D Euler codes. 
Nevertheless, this is a simple program that can be used for simple problems. 
The flow field in a two-dimensional or axisymmetric
inlet duct is solved by the method of characteristics.

The program asks for the name of the input file and proceeds to the end 
of the case. A file called inlet.out is produced as output. Two other
files are made that should be discarded.

This program was developed at NASA Ames around 1965. I was unable to locate
a copy of the source code, so I scanned it from the NASA document. 
There still may be a discrepancy between my scanned code and
the real thing. I would appreciate any bugs you find. The test case
diverges from the results shown in the original TN.
