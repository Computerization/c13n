OBJS   := $(patsubst %c,%o,$(wildcard *.c))
DEPS   := $(patsubst %c,%d,$(wildcard *.c))
TARGET := md2tex
CFLAGS += -Wno-macro-redefined -Wno-unused-command-line-argument -O2

ifeq ($(CC),emcc)
	TARGET := $(TARGET).js
	BYPROD := $(patsubst %js,%wasm,$(TARGET))
	CFLAGS += -sFORCE_FILESYSTEM=1 -sEXPORTED_RUNTIME_METHODS='["callMain","FS"]'
endif


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
	-rm $(OBJS) $(DEPS) $(TARGET) $(BYPROD)

-include $(DEPS)
