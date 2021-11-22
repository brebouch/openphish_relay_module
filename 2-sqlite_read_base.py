import sys
import sqlite3
	
def read_db(database,table):
	liste=[]
	with sqlite3.connect(database) as conn:
		cursor=conn.cursor()
		sql_request = f"SELECT * from {table}"
		try:
			cursor.execute(sql_request)
			for resultat in cursor:
				#print(resultat)		
				liste.append(resultat)
		except:
			sys.exit("couldn't read database")
	return(liste)

def main():
	database="database.db"
	table="observables"
	fichier_out=open('zresult.txt','w')
	resultats = read_db(database,table)	
	if resultats :
		for resultat in resultats:
			print(resultat)
			for item in resultat:			
				fichier_out.write(item)
				fichier_out.write(';')
		fichier_out.write('\n')
	else:
		print('NO RESULTS')
	fichier.close()
if __name__=='__main__':
	main()
