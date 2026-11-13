# General info

Simple tool for searching text in files. Only supports plain text files, no binary formats such as Word or PDF.

I was looking for a decent tool to search through my markdown files.  
Windows search however is too cumbersome. 

# Remarks

Currently only tested on Windows.

!! Deprecated.

From test branch.
New.


```mermaid
sequenceDiagram
    autonumber
    actor User
    participant App as Frontend App
    participant API as Auth Server
    participant DB as Database

    User->>App: Enter username & password
    App->>API: POST /login
    activate API
    API->>DB: Query user credentials
    activate DB
    DB-->>API: Return user record
    deactivate DB

    alt Valid Credentials
        API-->>App: 200 OK (JWT Token)
        App-->>User: Redirect to dashboard
    else Invalid Credentials
        API-->>App: 401 Unauthorized
        App-->>User: Show error message
    end
    deactivate API
```

