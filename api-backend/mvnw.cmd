@REM ----------------------------------------------------------------------------
@REM Licensed to the Apache Software Foundation (ASF) under one
@REM or more contributor license agreements.  See the NOTICE file
@REM distributed with this work for additional information
@REM regarding copyright ownership.  The ASF licenses this file
@REM to you under the Apache License, Version 2.0 (the
@REM "License"); you may not use this file except in compliance
@REM with the License.  You may obtain a copy of the License at
@REM
@REM    http://www.apache.org/licenses/LICENSE-2.0
@REM
@REM Unless required by applicable law or agreed to in writing,
@REM software distributed under the License is distributed on an
@REM "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
@REM KIND, either express or implied.  See the License for the
@REM specific language governing permissions and limitations
@REM under the License.
@REM ----------------------------------------------------------------------------

@REM ----------------------------------------------------------------------------
@REM Apache Maven Wrapper startup batch script, version 3.3.2
@REM
@REM Optional ENV vars
@REM   JAVA_HOME - location of a JDK home dir, required when download maven via java source
@REM   MVNW_REPOURL - repo url base for downloading maven binaries
@REM   MVNW_USERNAME/MVNW_PASSWORD - user and password for downloading maven binaries
@REM   MVNW_VERBOSE - true: enable verbose log; others: silence the output
@REM ----------------------------------------------------------------------------

@IF "%__MVNW_ARG0_NAME__%"=="" (SET __MVNW_ARG0_NAME__=%~nx0)
@SET __MVNW_CMD__=
@SET __MVNW_ERROR__=
@SET __MVNW_PSMODULEP_SAVE=%PSModulePath%
@SET PSModulePath=
@FOR /F "usebackq tokens=1* delims==" %%A IN ("%~dp0.mvn\wrapper\maven-wrapper.properties") DO @(
  IF "%%A"=="distributionUrl" SET "MVNW_DIST_URL=%%B"
)
@IF "%MVNW_DIST_URL%"=="" %__MVNW_CMD__% SET __MVNW_ERROR__=distributionUrl property not found in %~dp0.mvn\wrapper\maven-wrapper.properties& GOTO :ERROR
@IF "%~2"=="" GOTO :DONE_PARSE
:PARSE
@SET __MVNW_ARG__=%~1
@IF "%__MVNW_ARG__:~0,2%"=="-D" SET __MVNW_ARG__=%__MVNW_ARG__:~2%
@IF /I "%__MVNW_ARG__:~0,12%"=="distributionUrl" SET MVNW_DIST_URL=%__MVNW_ARG__:~16%
@SHIFT
@IF NOT "%~1"=="" GOTO :PARSE
:DONE_PARSE

@SET PSModulePath=%__MVNW_PSMODULEP_SAVE%
@SET MVNW_DIST_URLF=%MVNW_DIST_URL:/=\%
@SET MVNW_DIST_URLF=%MVNW_DIST_URLF:~6%

@SET "MAVEN_HOME=%USERPROFILE%\.m2\wrapper\dists\%MVNW_DIST_URLF%"
@IF EXIST "%MAVEN_HOME%" GOTO :EXEC_MVN

@SET "MVNW_TMP=%TEMP%\mvnw"
@IF EXIST "%MVNW_TMP%" RMDIR /S /Q "%MVNW_TMP%"
@MKDIR "%MVNW_TMP%" || GOTO :ERROR

@REM download maven
@IF DEFINED MVNW_VERBOSE (SET MVNW_QUIET=) ELSE SET MVNW_QUIET=--quiet
PowerShell -NoProfile -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%MVNW_DIST_URL%' -OutFile '%MVNW_TMP%\maven.zip'}"
IF %ERRORLEVEL% NEQ 0 %__MVNW_CMD__% SET __MVNW_ERROR__=Failed to download %MVNW_DIST_URL%& GOTO :ERROR

@REM unzip
PowerShell -NoProfile -Command "& {Expand-Archive '%MVNW_TMP%\maven.zip' '%MVNW_TMP%'}"
IF %ERRORLEVEL% NEQ 0 %__MVNW_CMD__% SET __MVNW_ERROR__=Failed to unzip maven& GOTO :ERROR

@REM move
@FOR /D %%G IN ("%MVNW_TMP%\*") DO @MOVE /Y "%%G" "%MAVEN_HOME%" >NUL
@IF EXIST "%MVNW_TMP%" RMDIR /S /Q "%MVNW_TMP%"

:EXEC_MVN
@SET "PATH=%MAVEN_HOME%\bin;%PATH%"

%MAVEN_HOME%\bin\mvn.cmd %*
@IF %ERRORLEVEL% NEQ 0 GOTO :ERROR
@GOTO :END

:ERROR
@IF "%__MVNW_ERROR__%"=="" @SET __MVNW_ERROR__=Apache Maven Wrapper encountered an error
@ECHO %__MVNW_ERROR__% >&2
@EXIT /B 1

:END
