from ldap3 import Server, Connection, ALL

def authenticate_user(username,password):
    #address = 'softinfi.online'
   address = '192.168.43.186'
   server = Server(address, get_info=ALL)
   #conn = Connection(server, 'cn='+username + ',dc=softinfi,dc=online', password)
   if username=='admin':
       conn = Connection(server,'cn='+username + ',dc=rpi, dc=com' ,password)
   else:
       conn = Connection(server,'cn='+username+', ou=Students, dc=rpi, dc=com' ,password)
   conn.bind()
   #conn.search('dc=rpi, dc=com', '(objectclass=person)')
   #return (conn.result['description'],conn.result['type'],)
   return True if conn.result ['description']=='success' else False

   #return True if username =='admin' else False


if __name__ == '__main__':
    username = input()
    password = input()
    print(authenticate_user(username,password))
