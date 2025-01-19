EXECUTABLE=ptoc
WINDOWS=$(EXECUTABLE).exe
VERSION=0.0.1

.PHONY: all build zip-win clean

all: build zip-win clean

build:
	env GOOS=windows GOARCH=amd64 go build -v -o $(WINDOWS) -ldflags="-s -w -X main.version=$(VERSION)" ./main.go

zip-win:
	zip $(EXECUTABLE)-$(VERSION).zip $(WINDOWS)

clean:
	rm -f $(WINDOWS)
