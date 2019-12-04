

DEV

    docker-compose up -d kafka
   ./populate-test-kafka.sh


    docker-compose up kafka-ui

 look at http://localhost:9000 to check 
    

    export FLASK_DEBUG=1
    FLASK_APP=logs.py flask run


