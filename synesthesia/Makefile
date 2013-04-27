CC=g++
CFLAGS=-g -c -Wall
LDFLAGS=-g -lzmq
SOURCES=main.cc
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=synesthesia

all: $(SOURCES) $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS)
	$(CC) $(OBJECTS) $(LDFLAGS) -o $@

.cpp.o:
	$(CC) $< $(CFLAGS) -o $@

clean:
	rm -rf *o $(EXECUTABLE)
