# Tech Writer Agent - C Implementation Makefile

CC = cc
CFLAGS = -Wall -Wextra -O2 -std=c99 -D_DEFAULT_SOURCE
LDFLAGS = -lcurl -lm

# Platform detection
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    CFLAGS += -D_GNU_SOURCE
endif
ifeq ($(UNAME_S),Darwin)
    # macOS specific flags
    CFLAGS += -I/opt/homebrew/include -I/usr/local/include
    LDFLAGS += -L/opt/homebrew/lib -L/usr/local/lib
endif
ifeq ($(OS),Windows_NT)
    # Windows specific flags
    CFLAGS += -D_WIN32_WINNT=0x0600
    LDFLAGS += -lws2_32
endif

# Source files
SRCDIR = src
SOURCES = $(SRCDIR)/main.c \
          $(SRCDIR)/agent.c \
          $(SRCDIR)/platform.c \
          $(SRCDIR)/http.c \
          $(SRCDIR)/tools.c \
          $(SRCDIR)/cJSON.c

OBJECTS = $(SOURCES:.c=.o)
EXECUTABLE = tech-writer

# Targets
all: $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS)
	$(CC) $(OBJECTS) -o $@ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(EXECUTABLE)

install: $(EXECUTABLE)
	install -m 755 $(EXECUTABLE) /usr/local/bin/

# Dependencies
$(SRCDIR)/main.o: $(SRCDIR)/main.c $(SRCDIR)/platform.h $(SRCDIR)/agent.h
$(SRCDIR)/agent.o: $(SRCDIR)/agent.c $(SRCDIR)/agent.h $(SRCDIR)/platform.h $(SRCDIR)/http.h $(SRCDIR)/tools.h $(SRCDIR)/cJSON.h
$(SRCDIR)/platform.o: $(SRCDIR)/platform.c $(SRCDIR)/platform.h
$(SRCDIR)/http.o: $(SRCDIR)/http.c $(SRCDIR)/http.h $(SRCDIR)/platform.h
$(SRCDIR)/tools.o: $(SRCDIR)/tools.c $(SRCDIR)/tools.h $(SRCDIR)/platform.h $(SRCDIR)/cJSON.h
$(SRCDIR)/cJSON.o: $(SRCDIR)/cJSON.c $(SRCDIR)/cJSON.h

.PHONY: all clean install