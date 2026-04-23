# CSCI-Assignment3


## GO GAME - Simple API

<strong> Response Format </strong>
```json
{
  "board_size": 5,
  "board": [
    [null, null, null, null, null],
    [null, "black", null, null, null],
    [null, null, "white", null, null],
    [null, null, null, null, null],
    [null, null, null, null, null]
  ],
  "current_player": "black",
  "black_score": 1,
  "white_score": 1,
  "consecutive_passes": 0,
  "move_number": 2,
  "game_over": false,
  "message": "Game started"
}
```


<strong>Create a Game: </strong> `create_game_state(size=5)`

* `size`: board size (1–26)

---

#### Player Moves Messages

Normal Move :

```json
{
  "type": "move",
  "move": "c3",
  "color": "black"
}
```

Pass Move : 

```json
{
  "type": "pass",
  "color": "white"
}
```

</br>

<strong>Apply Move</strong>

```
response = handle_move(state, move_msg)
state = response
```

</br>

<strong>Invalid Move</strong>
```json
{
  "ok": false,
  "message": "Illegal move: suicide is not allowed"
}
```

---

## API Response EXAMPLE

```json
{
  "ok": true,
  "board_size": 5,
  "board": [...],
  "current_player": "white",
  "black_score": 2,
  "white_score": 1,
  "consecutive_passes": 0,
  "move_number": 3,
  "game_over": false,
  "message": "black played c3"
}
```





