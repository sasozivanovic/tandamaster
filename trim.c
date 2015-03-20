#include <mp3splt.h>
#include <stdio.h>
#include <stdlib.h>

int trim(char* filename, long* start, long* end);

int main(int argc, char* argv[]) {
  if (argc != 2)
  {
    fprintf(stderr, "Please provide the input file to be split as the first argument.\n");
    fflush(stderr);
    return EXIT_FAILURE;
  }
  long start, end;
  splt_code error = trim(argv[1], &start, &end);
  if (error) {
    printf("Error %d!\n", error);
  }
  printf("%d - %d\n", start, end);
}

int trim(char* filename, long* start, long* end) {
  splt_code error = SPLT_OK;
  
  splt_state *state = mp3splt_new_state(NULL);
  
  error = mp3splt_find_plugins(state);
  if (error) return (int) error;
  
  mp3splt_set_filename_to_split(state, filename);
  
  error = mp3splt_set_trim_silence_points(state);
  if (error) return (int) error;
  
  splt_points *points = mp3splt_get_splitpoints(state, &error);
  if (error) return (int) error;
  
  mp3splt_points_init_iterator(points);

  const splt_point* point = mp3splt_points_next(points);
  *start = mp3splt_point_get_value(point);

  point = mp3splt_points_next(points);
  *end = mp3splt_point_get_value(point);

  point = mp3splt_points_next(points);
  if (point) {
    printf("Warning: more than two splitpoints!");
  }
  
  mp3splt_free_state(state);

  return (int) SPLT_OK;
}

