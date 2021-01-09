import subprocess
class rarHandler:
    async def listArchive(archive):
        output = []
        try:
            cmdOutput = subprocess.check_output('unrar lb {0}'.format(archive), shell=True) #extract the file
            cmdOutput = cmdOutput.decode()
            output = cmdOutput.split("\n")
            output = output[:len(output)-1] #remove the '' last element in the list
        except subprocess.CalledProcessError:
            print("ERROR!!")
        return output

    async def extractArchive(archive,extractLocation):
        try:
            print(subprocess.check_output('cd {1} && unrar x -kb -y {0}'.format(archive,extractLocation), shell=True)) #extract the file
        except subprocess.CalledProcessError:
            print("ERROR!!")