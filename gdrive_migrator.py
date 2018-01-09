import commands
import subprocess
import os, logging, sys, signal, time, shutil
import getpass

##################################################################################
# Variables
##################################################################################  
userName = os.getlogin()
googleDriveDir = ""
gdfsInstaller = "/Library/Scripts/Workday/GoogleDriveFileStream.dmg"
# Logging File 
#logFile = "/Library/Logs/Workday/googleDrive_Migration.log"
logFile = "/Users/" + userName + "/Library/Logs/Workday/googleDrive_Migration.log"
basedir = os.path.dirname(logFile)
if not os.path.exists(basedir):
    os.makedirs(basedir)
if not os.path.exists(logFile):
    with open(logFile, 'a'):
        os.utime(logFile, None)

logging.basicConfig(filename=logFile, level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s')
# Console Handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)  
gstream = "/Applications/Google Drive File Stream.app"
gdrive = "/Applications/Google Drive.app"

##################################################################################
# Functions
##################################################################################  
def appExist(appName):
    logging.info("Checking for the existence of: %s", appName)
    return os.path.exists(appName)

def appProcessID(appPath, action):
    # the "action" item takes either a "kill" or "check" action.
    global appName
    appName = os.path.splitext(os.path.basename(appPath))[0]
    logging.debug('AppName variable and action to be taken is: %s, %s', appName, action)
    if action == "check":
        logging.info('Looking for Process ID(s) for %s', appName)
        process = subprocess.Popen(['pgrep', '-i', appName], stdout=subprocess.PIPE)
        global my_pid
        my_pid, err = process.communicate()
        # Check if the application is running and log status
        #my_pid = appProcessID(gdrive)
        if my_pid:
            logging.debug('Application %s is running with process ID(s): %s', gdrive, my_pid)   
        else:
            logging.debug('Application %s, is not running. Could not find any process id(s)', appName)
        return my_pid
    elif action == "kill":
        if not my_pid:
            appExit('No Process ID was found.')
        try:
            pid = int(my_pid)
            logging.debug('Converted %s to an integar acceptable for signal killing.', pid)
            #print "that worked"
        except ValueError:
            appExit('Could not confirm ' + my_pid + 'as an integar value acceptable for signal kill.')
            appExit
            #print "did not work"
        os.kill(pid, signal.SIGKILL)    
    else:
        appExit('Could not run the function appProcessID wihtout an action argument.')
    
    
def googleDirLookup(directory):
    #UsersGoogleDriveDir = "/Users/" + userName + "/" + appName + "/"
    logging.info('Verifying if this path exists: %s', directory)
    if os.path.exists(directory):
        googleDriveDir = directory
        if os.path.islink(googleDriveDir):
            dir = os.path.realpath(googleDriveDir)
            googleDriveDir = dir + "/"
            logging.info('The path was a symlink and has been updated to use the real path.')
        else:
            googleDriveDir = directory + "/"
        logging.info('Found the directory %s', googleDriveDir)
        return googleDriveDir
    else:
        logging.info('Could not find the path: %s', directory)
def renameDir(olddir, newdir):
    logging.info('Renaming %s to %s', olddir, newdir)
    os.rename(olddir, newdir)
    time.sleep(3)

def Uninstall(appName):
    logging.info('Killing any processes from %s', appName)
    appProcessID(appName, "kill")
    logging.info('Checking if process was killed successfully...')
    appProcessID(appName, "check")
    logging.info('Deleting %s...', appName)
    time.sleep(5)
    if os.path.exists(appName):
        shutil.rmtree(appName)
    else:
        logging.info('Could not find the path: %s', appName)
    # Rename Google Drive folder if it exists
    if not os.path.exists(RenamedUsersGoogleDriveDir):
        renameDir(UsersGoogleDriveDir, RenamedUsersGoogleDriveDir)
        appExit('Successful! New path is set to ' + RenamedUsersGoogleDriveDir)
    else:
        appExit('Failed! Could not find the path: ' + RenamedUsersGoogleDriveDir)

    
def openFileCheck(directory):
    p1=subprocess.Popen(['lsof', '-Fn'], stdout=subprocess.PIPE)
    p2=subprocess.Popen(['grep', directory + "/"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p3=subprocess.Popen(['grep', '-v', '.DS_Store'], stdin=p2.stdout, stdout=subprocess.PIPE)
    process = p3.communicate()[0]
    if process:
        return process

def installApp(appName):
    if not appExist(appName):
        print appName
        appExit('FAILED to find the installer from ' + appName)
    mountedGDFS = "/Volumes/GoogleDriveFileStream"
    logging.info('Found %s...mounting to %s...', appName, mountedGDFS)
    # Mount DMG
    p1=subprocess.Popen(['hdiutil', 'attach', '-mountpoint', mountedGDFS, appName], stdout=subprocess.PIPE).wait()
    if not os.path.exists(mountedGDFS + "/GoogleDriveFileStream.pkg"):
        appExit('FAILED to mount directory')
    gdfsPKG = mountedGDFS + "/GoogleDriveFileStream.pkg"
    logging.info('Successfully mounted %s.', mountedGDFS)
    logging.info('Installing PKG from %s...', gdfsPKG)
    p1=subprocess.Popen(['installer', '-pkg', gdfsPKG, '-target', '/'], stdout=subprocess.PIPE).wait()
    if not appExist(gstream):
        p2=subprocess.Popen(['hdiutil', 'attach', '-mountpoint', mountedGDFS, appName], stdout=subprocess.PIPE).wait()
        appExit('FAILED could not find Google Drive File Stream in ' + gstream)
    # Detach mounted DMG
    logging.info('Unmounting Installer DMG...')
    d1=subprocess.Popen(['df', '-h'], stdout=subprocess.PIPE)
    d2=subprocess.Popen(['grep', mountedGDFS], stdin=d1.stdout, stdout=subprocess.PIPE)
    diskDrive =  d2.stdout.readline()[0:12]
    detachCommand=subprocess.Popen(['hdiutil', 'detach', diskDrive], stderr=subprocess.PIPE, stdout=subprocess.PIPE).wait()
    if not os.path.exists(mountedGDFS):
        logging.info('Successfully unmounted %s', appName)
    else:
        logging.info('Failed to unmount %s', appName)

def appExit(exitstatement):
    logging.info("%s", exitstatement)
    logging.info('==============END==========================')
    logging.info(' ')
    sys.exit()

##################################################################################
# Check Logic
##################################################################################  
# Check and create log files if they do not exist.
logging.info('==============START========================')
logging.info('Location of logs: %s', logFile)
logging.info('Current logged in user: %s', userName)

# Check for the existence of the application before installing.
logging.info('Checking for the existence of application: %s', gstream)
gStreamExist = "FALSE"
if os.path.isdir(gstream):
    gStreamExist="TRUE"
    # DO NOT EXIT HERE FOR PRODUCTION
    #appExit(gstream + ", is installed on this system, no need to continue.")
logging.info('Could not find the application: %s', gstream)

# Check if Google Drive is installed.
logging.info('Checking for the existence of application: %s', gdrive)
gDriveExist = "TRUE"
if not os.path.isdir(gdrive):
    gDriveExist="FALSE"
    # DO NOT EXIT HERE FOR PRODUCTION
    #appExit(gdrive + ", is installed on this system")
logging.info('Found the application: %s', gdrive)

# Check if the application is running and log status
appProcessID(gdrive, "check")

# Check for Google Drive folder and for any open files from the application's directory.
UsersGoogleDriveDir = "/Users/" + userName + "/" + appName
RenamedUsersGoogleDriveDir = os.path.dirname(UsersGoogleDriveDir) + "/.RENAMED_" + appName
folderRenamed = "FALSE"
if googleDirLookup(UsersGoogleDriveDir):
    logging.info('Checking to see if any open files exist for %s in %s', appName, UsersGoogleDriveDir)
    openFiles = openFileCheck(UsersGoogleDriveDir)
    if openFiles:
        logging.debug('Currently open files include: %s', openFiles)
        appExit("Found actively open files in the directory. Cannot continue at this time.  Quitting script...")
    logging.info('No open files found, continuing...')
elif googleDirLookup(RenamedUsersGoogleDriveDir):
    logging.info('Already renamed user\'s home folder.  No need to continue.')
    folderRenamed = "TRUE"
else:
    logging.info('No Google Drive folder found in users home directory.')

##################################################################################
# Action Logic
##################################################################################  
if gStreamExist =='FALSE' and gDriveExist =='FALSE' and folderRenamed =='FALSE':
    # Install Google Drive File Stream
        # 1) Check if installer is in place
        # 2) Install if found
    logging.info('== Taking action to Install Google Drive File Stream ==')
    installApp(gdfsInstaller)
    appExit('Successful!')
elif gStreamExist =='FALSE' and gDriveExist =='TRUE' and folderRenamed =='FALSE':
    logging.info('== Taking action to Install GDFS & Uninstall GDrive ==')
    # Install Google Drive File Stream
        # 1) Check if installer is in place
        # 2) Install if found
    installApp(gdfsInstaller)
    # Uninstall Google Drive 
    # 1) Kill Process
    # 2) Remove delete application from Applications folder
    # 3) Rename Google Drive folder in user's home directory
    Uninstall(gdrive)
    appExit('Successful!')
elif gStreamExist =='TRUE' and gDriveExist =='TRUE' and folderRenamed =='FALSE':
    logging.info('== Taking action to Uninstall Gdrive ==')
    # Uninstall Google Drive 
    # 1) Kill Process
    # 2) Remove delete application from Applications folder
    # 3) Rename Google Drive folder in user's home directory
    Uninstall(gdrive)
    appExit('Successful!')
elif gStreamExist =='TRUE' and gDriveExist =='FALSE' and folderRenamed =='FALSE':
    logging.info('== Taking action to Rename Gdrive Directory ==')
    # 3) Rename Google Drive folder in user's home directory
    renameDir(UsersGoogleDriveDir, RenamedUsersGoogleDriveDir)
    appExit('Successful!')
#else gStreamExist =='TRUE' and gDriveExist =='FALSE' and folderRenamed =='TRUE':
    # Ideal scenario, do nothing!
else:
    appExit('== NO ACTION TAKEN: Google Drive File Stream is installed, Google Drive is uninstalled, and ' + userName + " Google Drive folder is renamed.")
