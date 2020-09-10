REST-JPG
========

[![Build status][github-actions-image]][github-actions-url]
[![license][license-image]][license-url]

Course project for the course
[052533 - Middleware Technologies For Distributed Systems][project-course] held
in the autumn semester of 2020 at [Politecnico di Milano][polimi].


Documentation
-------------

Documentation for the REST API is available through Postman [**here**][api-doc]<sup>*</sup>. Browse examples online or try it out using [Postman's native app][postman-app].

<sup>* Link may expire after course final grading.</sup>


Running the server
------------------

### Development

In *development* mode, the server creates a new volatile database and save
images inside the container only. All data is lost on shutdown. The server will
listen for HTTP connections on port 80.

To run in this mode, first build with `docker-compose build` and then `run` the
`server` service passing `--test` as first argument.

```
$ docker-compose build
$ docker-compose run --service-ports --rm server --test
```

### Production

In *production* mode, the server uses the DB present at `./db/db.sqlite` (if not
present, a new one is created) and saves images in the `./images` directory.
Data persists after shutdown. The server will listen for HTTPS connections on
port 443, using the HTTPS certificates provided in the `./https` folder.

```
$ docker-compose up -d
```


Testing
-------

Unit tests are implemented in the `tests/` folder. To run tests, start the
server in *development* mode and then start the `test.py` script from within the
`test/` directory.

```
$ docker-compose run --service-ports --rm server --test

# in another shell
$ cd test
$ pip3 install --user -r requirements.txt # if needed
$ ./test.py
```

NOTE: the `test_client.py` is used to test OAuth functionality, it will create
a temporary HTTP server listening on port 9999 for this purpose when token
generation tests are run.


---
This project is distributed under the terms of the Apache License v2.0.
See file [`LICENSE`][license] for further reference.


[github-actions-url]: https://github.com/mebeim/middleware_project/actions
[github-actions-image]: https://github.com/mebeim/middleware_project/workflows/CI/badge.svg?branch=master
[license-url]: https://github.com/mebeim/middleware_project/blob/master/LICENSE.md
[license-image]: https://img.shields.io/badge/license-Apache%202.0-green
[project-course]: https://www11.ceda.polimi.it/schedaincarico/schedaincarico/controller/scheda_pubblica/SchedaPublic.do?&evn_default=evento&c_classe=694795&polij_device_category=DESKTOP&__pj0=0&__pj1=7908374dbcd5f0ff305b0e84491f033b
[polimi]: https://www.polimi.it/
[api-doc]: https://documenter.getpostman.com/view/12652042/TVCmQjJz
[postman-app]: https://www.postman.com/downloads/
[license]: https://github.com/mebeim/middleware_project/blob/master/LICENSE
