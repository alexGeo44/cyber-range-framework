WORKLOAD_CATALOG = {
    "web": {
        "image": "nginx:alpine",
        "port": 80,
        "service": True,
        "allowed_node_types": ["cloud", "fog", "edge"],
    },

    "api": {
        "image": "hashicorp/http-echo:latest",
        "port": 5678,
        "service": True,
        "allowed_node_types": ["cloud", "fog"],
    },

    "database": {
        "image": "postgres:alpine",
        "port": 5432,
        "service": True,
        "allowed_node_types": ["cloud"],
        "env": [
            {
                "name": "POSTGRES_PASSWORD",
                "value": "cyberrange"
            }
        ],

    },
}

