
#!/usr/bin/env python
"""wp2hugo.python convert wodrpess database to hugo markdown format"""
__version__ = "0.0.1"
__author__ = "Kiichi Takeuchi"
__copyright__ = "(C) 2015 Kiichi Takeuchi. GNU GPL 3."
__contributors__ = ["Kiichi Takeuchi"]


# ----------------------------------------------------------------
import html2text
import MySQLdb
import sys
import os
import datetime
import argparse

# ----------------------------------------------------------------
parser = argparse.ArgumentParser(description='Convert Wordpress Database to Markdown for Hugo CMS')
parser.add_argument('-o','--output', dest='output', help='Output folder name. If the folder is not there, it will create. Leave this blank for dry-run.')
parser.add_argument('-s','--server', required=True, help='Server URL or Unix Socket Path')
parser.add_argument('-d','--database', required=True, help='WordPress Database name')
parser.add_argument('-u','--username', required=True, help='WordPress Database Username')
parser.add_argument('-p','--password', required=True, help='WordPress Database Passwordn')
parser.add_argument('-l','--limit', help='Limit the number of records to process if you need to specify')
parser.add_argument('--image_base_url_old', help='Old Wordpress Image URL')
parser.add_argument('--image_base_url_new', help='Old Wordpress Image URL')
args = parser.parse_args()
#print(args.output)
#print(args)

# ----------------------------------------------------------------
dest = ''
if args.output:
	dest = args.output

limit = ''
if args.limit:
	limit = " LIMIT " + args.limit

# ----------------------------------------------------------------
# DB Config
# to find unix socket file of mysql,  run this in console 
# to figure out where the socket file is
# mysql_config --socket
conn = None
if args.server.find('.sock') > 0:
	conn = MySQLdb.connect(unix_socket=args.server,
				user=args.username,
				passwd=args.password,
				db=args.database)
else:
	conn = MySQLdb.connect(host=args.server,
			user=args.username,
			passwd=args.password,
			db=args.database)
			
# ----------------------------------------------------------------
# Color code for console 
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = "\033[1m"

# ----------------------------------------------------------------
# Code below
# My memo:
# according to their doc, section and slug  should contrib the file path?
#http://gohugo.io/content/organization/
#http://gohugo.io/content/front-matter/
#or should this be in config level thing like
#http://gohugo.io/extras/permalinks/

#additional meta
#tags = ["x", "y"]
#categories = ["x", "y"]
#date = "2015-01-12T19:20:04-07:00"
#weight = 4
#help=''
#topics=['','']
#
# can i do this?
#section="{{{post_category}}}"

md_template = '''
+++
date = "{{{post_date}}}"
draft = false                                                                                                                                                                                                    
title = "{{{post_title}}}"
slug="{{{post_name}}}"
+++
{{{post_content}}}
'''
try :
	cur = conn.cursor(MySQLdb.cursors.DictCursor)
	result = cur.execute('''SELECT
				po.ID,
				po.post_title,
				po.post_content,
				po.post_date,
				us.display_name,
				po.post_type,
				po.post_name
				FROM wp_posts po, wp_users us 
				WHERE po.post_author=us.ID 
				AND post_status='publish'
				AND post_type IN ('page','post')
				ORDER BY po.ID
				''' + limit)

	rows = cur.fetchallDict()
	print ENDC
	efile = open('error.txt',"w")
	total = len(rows)
	error_count = 0
	warning_count = 0
	
	for row in rows:
		dest_sub = os.path.join(dest,row['post_type'])
		try:
			os.makedirs(dest_sub)
		except:
			pass

		file_path = os.path.join(dest_sub,row["post_name"] + ".md")
		post_id = row["ID"]
		try:
			f = open(file_path,"w")
			md = md_template
			num_bytes = 0
			#print(row)
			for col in row.keys():	
				if col == "post_content":
					#print(row['post_content'])
					#post_content = html2text.html2text(row['post_content'].decode('utf8'))
					post_content = row['post_content'].decode('utf8','ignore')
					if args.image_base_url_old:
						post_content = post_content.replace(args.image_base_url_old,args.image_base_url_new)
					post_content = html2text.html2text(post_content)
					#unicode(str, errors='ignore')
					num_bytes = len(post_content)
					md = md.replace("{{{post_content}}}",post_content)
				elif col == "post_date":
					post_date = row['post_date'].isoformat()+"-05:00" # East Coast?
					md = md.replace("{{{post_date}}}",post_date)
				else:
					md = md.replace("{{{"+col+"}}}",str(row[col]).replace('"','\\"'))
			#print(md)	
			f.write(md)
			f.close()
			if num_bytes < 10:
				print '[',WARNING,'WARNING',ENDC,']	',file_path ,WARNING,str(num_bytes),'bytes',ENDC
				warning_count = warning_count + 1
			else:
				print '[',OKGREEN,'OK',ENDC,']	',file_path ,str(num_bytes),'bytes'
		except Exception as ex:
			print '[',FAIL,'ERROR',ENDC,']	',file_path,str(num_bytes),'bytes'
			efile.write(file_path + " (" + str(post_id) + ") ")
			efile.write(str(ex) + "\n")
			error_count = error_count + 1
			#raise
	efile.close()
finally:
	conn.close()
print "========================================================"
print HEADER,"Total: ", total,ENDC,"/",OKGREEN,"OK:",(total-error_count-warning_count), ENDC,"/",WARNING,"Warning:",warning_count,ENDC,"/",FAIL,"Error:",error_count,ENDC
print "========================================================"
print "See error.txt for more details"
