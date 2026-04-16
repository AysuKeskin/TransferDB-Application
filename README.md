export DB_USER='root'
export DB_PASSWORD=''
export DB_NAME='DB'


mysql -uroot -p < sql/schema.sql                                                               
mysql -uroot -p DB < sql/seed_data.sql      
mysql -uroot -p DB < sql/triggers.sql

mysql -uroot -p