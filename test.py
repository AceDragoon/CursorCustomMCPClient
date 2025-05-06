{
  "sqlite": [
    [
      {
        "name": "read_query",
        "description": "Execute SELECT",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string"
            },
            "server": {
              "title": "sqlite",
              "type": "string"
            }
          },
          "required": [
            "query",
            "server"
          ]
        }
      }
    ],
    [
      {
        "uri": "memo://insights",
        "name": "Business Insights Memo",
        "description": "Insights",
        "mimeType": "text/plain",
        "size": null,
        "annotations": null,
        "server": "sqlite"
      }
    ],
    [
      {
        "name": "mcp-demo",
        "description": "Seed DB",
        "arguments": [
          {
            "name": "topic",
            "description": null,
            "required": true
          }
        ],
        "server": "sqlite"
      }
    ]
  ],
  "NotizenAssistent": [
    [
      {
        "name": "add",
        "description": "Add two numbers",
        "inputSchema": {
          "properties": {
            "a": {
              "title": "A",
              "type": "integer"
            },
            "b": {
              "title": "B",
              "type": "integer"
            },
            "server": {
              "title": "Server",
              "type": "string"
            }
          },
          "required": [
            "a",
            "b",
            "server"
          ],
          "title": "NotizenAssistent",
          "type": "object"
        }
      }
    ],
    [
      {
        "uri": "text://greeting",
        "name": "text://greeting",
        "description": "Ein freundlicher Gruß",
        "mimeType": "text/plain",
        "size": null,
        "annotations": null,
        "server": "NotizenAssistent"
      },
      {
        "uri": "time://now",
        "name": "time://now",
        "description": "Aktuelle Serverzeit",
        "mimeType": "text/plain",
        "size": null,
        "annotations": null,
        "server": "NotizenAssistent"
      }
    ],
    [
      {
        "name": "simple_greeting",
        "description": "Generiere eine nette Begrüßung",
        "arguments": [
          {
            "name": "name",
            "description": null,
            "required": true
          }
        ],
        "server": "NotizenAssistent"
      }
    ]
  ]
}