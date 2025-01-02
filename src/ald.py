import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Expected Input File Name")
        exit(1)
    if len(sys.argv) < 3:
        print("Expected Output Name")
        exit(1)

    Objects = []
    if len(sys.argv) > 3:
        for i in range(len(sys.argv) - 2):
            Objects.append(sys.argv[i + 1])
    else:
        Objects.append(sys.argv[1])

    OutName = sys.argv[len(sys.argv) - 1]
    Out = open(OutName, "wb")

    for InName in Objects:
        File = open(InName, "rb")
        Out.write(File.read())
        File.close()

    Out.close()
