OBJS   := $(patsubst %c,%o,$(wildcard *.c))
DEPS   := $(patsubst %c,%d,$(wildcard *.c))
TARGET := md2tex
CFLAGS += -Wno-macro-redefined -O2

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c
	$(CC) -c $(CFLAGS) -o $@ $<

%.d: %.c
	@set -e; rm -f $@; \
	$(CC) -MM $(CFLAGS) $< > $@.$$$$; \
	sed 's,\($*\)\.o[ :]*,\1.o $@ : ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

.PHONY: clean
clean:
	-rm $(OBJS) $(DEPS) $(TARGET)

-include $(DEPS)
