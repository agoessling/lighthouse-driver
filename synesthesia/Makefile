CC=g++
CFLAGS=-g -c -Wall
LDFLAGS=-g -lzmq -lprotobuf
SOURCES=main.cc lh.cc lighthouse.pb.cc
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=synesthesia

all: $(SOURCES) $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS)
	$(CC) $(OBJECTS) $(LDFLAGS) -o $@

.cpp.o:
	$(CC) $< $(CFLAGS) -o $@

clean:
	rm -rf *o $(EXECUTABLE)
