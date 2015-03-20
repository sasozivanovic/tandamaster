%module trim
%include typemaps.i
%apply long &OUTPUT { long * start, long * end };
%{
#include <mp3splt.h>
extern int trim(char* filename, long* start, long* end);
%}

extern int trim(char* filename, long* start, long* end);
