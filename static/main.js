$(document).ready(() => {

    if ($('#game').length) {
        let webSocket,
            table = $('#gameEnemyFieldTable'),
            gameID = JSON.parse($('#gameID').text()),
            userID = JSON.parse($('#userID').text()).toString(),
            gameStatus = $('#gameStatus'),
            messages = $('#chatMessages'),
            messageInput = $('#messageInput'),
            messageSubmit = $('#messageSubmit'),
            webSocketSend = async (webSocket, data) => {
                webSocket.send(JSON.stringify(data));
            },
            messageAppend = (username, content, date) => {
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
            messageClear = () => {
                messages.empty()
            };

        // Chat
        messageInput.focus();

        function startWebsocket() {
            webSocket = new WebSocket(`ws://${window.location.host}/ws/game/${gameID}/`);

            webSocket.onmessage = function (e) {
                let response = JSON.parse(e.data);
                console.log(response);
                console.log(userID);

                if (response.type === 'message') {
                    messageAppend(response.username, response.content, response.date)
                } else if (response.type === 'history' && response.user_id === userID) {
                    messageClear();
                    for (let message_info of response.data) {
                        messageAppend(message_info.username, message_info.content, message_info.date)
                    }
                } else if (response.type === 'game_start' && response.user_id === userID) {
                    let boatPlaces = response.data.boat_places,
                        myAttackedFields = response.data.my_attacked_fields,
                        enemyAttackedFields = response.data.enemy_attacked_fields,
                        turn = response.data.turn;

                    if (turn === userID.toString()) {
                        gameStatus.text('Ваш ход')
                    } else {
                        gameStatus.text('Ходит противник')
                    }

                    for (let boatPlace of boatPlaces) {
                        let field = $(`#gameMyFieldTable #${boatPlace}`);
                        field.attr('class', 'boat')
                    }

                    for (let myAttackedField in myAttackedFields) {
                        let field = $(`#gameMyFieldTable #${myAttackedField}`);
                        field.attr('class', myAttackedFields[myAttackedField])
                    }

                    for (let enemyAttackedField in enemyAttackedFields) {
                        let field = $(`#gameEnemyFieldTable #${enemyAttackedField}`);
                        field.attr('class', enemyAttackedFields[enemyAttackedField])
                    }

                } else if (response.type === 'game' && response.user_id === userID) {
                    if (response.status === 'OK') {
                        let enemyField = $(`#gameEnemyFieldTable #${response.data['field']}`),
                            myField = $(`#gameMyFieldTable #${response.data['field']}`),
                            hit = response.data['hit'],
                            fromEnemy = response.data['from_enemy'],
                            attackedAlready = response.data['attacked'];
                        console.log(response);

                        if (fromEnemy) {
                            if (hit) {
                                myField.attr('class', 'hit')
                            } else {
                                myField.attr('class', 'miss')
                                gameStatus.text('Ваш ход')
                            }
                        } else {
                            if (!attackedAlready) {
                                if (hit) {
                                    enemyField.attr('class', 'hit')
                                } else {
                                    enemyField.attr('class', 'miss')
                                    gameStatus.text('Ходит противник')
                                }
                            } else {
                                alert('Поле уже было атаковано')
                            }
                        }

                    } else if (response.status === 'ERROR') {
                        alert(response.data['error_text']);
                    }
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
                if (field.hasClass('attacked')) {
                    alert('nonono')
                } else {
                    await webSocketSend(webSocket, {
                            type: 'gameAttack',
                            data: {
                                fieldID: field.attr('id'),
                                userID
                            }
                        }
                    )
                }
            }
        )

        // Game
    }
});