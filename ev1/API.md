# Robot Simulation API Documentation

This document outlines the API endpoints and data structures for interacting with the Robot Simulation server.

## Base URL

All API requests should be made to:

http://localhost:8585

## Endpoints

### 1. GET /

Retrieves the current state of the simulation.

#### Request

- Method: GET
- URL: `http://localhost:8585/`
- Headers: None required

#### Response

The response is a JSON object with the following structure:

```
{
  "robot_actions": [
    {
      "id": int,
      "action": string,
      "position": [int, int],
      "direction": [int, int],
      "robot_grab_id": int or null,
      "stack_coord": int or null (only present if action is "stack")
    },
    ...
  ],
  "box_positions": [
    {
      "id": int,
      "position": [int, int],
      "action": string,
      "num_boxes": int
    },
    ...
  ]
}
```
- `robot_actions`: An array of objects, each representing a robot's current state.
  - `id`: The unique identifier of the robot.
  - `action`: The current action of the robot (e.g., "move", "grab", "stack").
  - `position`: An array of two integers representing the robot's x and y coordinates.
  - `direction`: An array of two integers representing the robot's facing direction.
  - `robot_grab_id`: The ID of the box the robot is currently grabbing, or null if not grabbing.
  - `stack_coord`: The ID of the box being stacked on (only present if the action is "stack").

- `box_positions`: An array of objects, each representing a box or stack of boxes.
  - `id`: The unique identifier of the box or stack.
  - `position`: An array of two integers representing the box's x and y coordinates.
  - `action`: The current state of the box ("idle" or "stacked").
  - `num_boxes`: The number of boxes in this stack (1 for single boxes).

### 2. POST /

Updates the state of a specific robot in the simulation.

#### Request

- Method: POST
- URL: `http://localhost:8585/`
- Headers: 
  - Content-Type: application/json
- Body:

{
  "id": int,
  "position": [int, int],
  "direction": [int, int]
}

- `id`: The unique identifier of the robot to update.
- `position`: An array of two integers representing the new x and y coordinates for the robot.
- `direction`: An array of two integers representing the new facing direction for the robot.

#### Response

The response structure is identical to the GET response, reflecting the updated state of the simulation after the robot's movement.

## Usage in Unity

To interact with this API in Unity, you can use the `UnityWebRequest` class. Here are example snippets for both GET and POST requests:

### GET Request
```
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;

public class SimulationClient : MonoBehaviour
{
    private const string baseUrl = "http://localhost:8585";

    IEnumerator GetSimulationState()
    {
        using (UnityWebRequest webRequest = UnityWebRequest.Get(baseUrl))
        {
            yield return webRequest.SendWebRequest();

            if (webRequest.result == UnityWebRequest.Result.Success)
            {
                string jsonResponse = webRequest.downloadHandler.text;
                // Parse and process the JSON response here
                Debug.Log(jsonResponse);
            }
            else
            {
                Debug.LogError("Error: " + webRequest.error);
            }
        }
    }
}
```
### POST Request

```IEnumerator UpdateRobotState(int robotId, Vector2Int newPosition, Vector2Int newDirection)
{
    string jsonBody = JsonUtility.ToJson(new 
    {
        id = robotId,
        position = new int[] { newPosition.x, newPosition.y },
        direction = new int[] { newDirection.x, newDirection.y }
    });

    using (UnityWebRequest webRequest = new UnityWebRequest(baseUrl, "POST"))
    {
        byte[] jsonToSend = new System.Text.UTF8Encoding().GetBytes(jsonBody);
        webRequest.uploadHandler = new UploadHandlerRaw(jsonToSend);
        webRequest.downloadHandler = new DownloadHandlerBuffer();
        webRequest.SetRequestHeader("Content-Type", "application/json");

        yield return webRequest.SendWebRequest();

        if (webRequest.result == UnityWebRequest.Result.Success)
        {
            string jsonResponse = webRequest.downloadHandler.text;
            // Parse and process the JSON response here
            Debug.Log(jsonResponse);
        }
        else
        {
            Debug.LogError("Error: " + webRequest.error);
        }
    }
}
```
To use these methods, you can call them using `StartCoroutine(GetSimulationState())` or `StartCoroutine(UpdateRobotState(1, new Vector2Int(5, 5), new Vector2Int(0, 1)))` from another method in your Unity script.

Remember to handle the JSON responses appropriately in your Unity client to update the game state and visualizations based on the received data.