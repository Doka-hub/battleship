$(document).ready(() => {

    if ($('#game').length) {
        let webSocket,
            table = $('#gameFieldTable'),
            gameID = JSON.parse($('#gameID').text()),
            userID = JSON.parse($('#userID').text()),
            turn,
            messages = $('#chatMessages'),
            messageInput = $('#messageInput'),
            messageSubmit = $('#messageSubmit'),
            webSocketSend = async (webSocket, data) => {
                webSocket.send(JSON.stringify(data));
            },
            messageAppend = (username, content, date) => {
                console.log(content);
                messages.append(`
                    <div class="chat__message">
                        <div class="chat__message-username">
                            ${username}
                        </div>
                        <div class="chat__message-date">
                            ${date}
                        </div>
                        <div class="chat__message-content">
                            ${content}
                        </div>
                    </div>
                `)
            },
            messageClear = async () => {
                messages.empty()
            };

        // Chat
        messageInput.focus();
        // messageInput.keyup(function(e) {
        //     if (e.keyCode === 13) {  // enter, return
        //         messageSubmit.click();
        //     }
        // });

        function startWebsocket() {
            webSocket = new WebSocket(`ws://${window.location.host}/ws/game/${gameID}/`);

            webSocket.onmessage = function (e) {
                let data = JSON.parse(e.data);
                if (data.type === 'message') {
                    messageAppend(data.username, data.content, data.date)
                } else if (data.type === 'history' && data.user_id === userID) {
                    messageClear();
                    for (let message_info of data.data) {
                        messageAppend(message_info.username, message_info.content, message_info.date)
                    }
                } else if (data.type === 'game' && data.user_id === userID) {
                    console.log(data);
                    if (data.status === 'OK') {
                        turn = data.data['turn'];
                    } else if (data.status === 'ERROR') {
                        alert(data.data['error_text']);
                    }
                } else if (data.type === 'game_start' && data.user_id === userID) {
                    console.log(data.data)
                }
            };

            webSocket.onclose = function (e) {
                if (e.code !== 1000) {  // если соед. закрыто ненамеренно
                    webSocket = null;
                    setTimeout(startWebsocket, 2000)
                }
            }
        }

        startWebsocket();

        messageSubmit.click(async (e) => {
            let message = messageInput.val();

            await webSocketSend(webSocket, {type: 'message', message});

            messageInput.val('')
        });

        // Chat


        // Game

        table.find('td').click(
            async (e) => {
                let field = $(e.target);
                // if (userID === turn) {
                    await webSocketSend(webSocket, {
                            type: 'gameAttack',
                            data: {
                                fieldID: field.attr('id'),
                                userID
                            }
                        }
                    )
                // } else {
                //     alert('Не ваш ход!')
                // }
            }
        )

        // Game
    }
});