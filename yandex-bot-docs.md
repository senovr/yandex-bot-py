# Bot API для Мессенджера в Яндекс 360 для бизнеса

Документация собрана автоматически

---

# О сервисе

Все операции автоматизации в Мессенджере выполняются через Bot API. Доступ к API осуществляется от лица бота. Бот авторизует все операции с помощью OAuth-токена.

## Создание бота

Бот для организации создается в Яндекс 360 для бизнеса на странице [Боты в Мессенджере](https://admin.yandex.ru/bot-platform). Токен для бота создается там же. Подробнее о том, как это сделать, читайте в разделе [Боты в Мессенджере](https://yandex.ru/support/yandex-360/business/admin/ru/messenger/bot-platform#bot-create) Справки Яндекс 360 для бизнеса.



---

# Создание чата или канала

- [Заголовки](ru/api-requests/chat-create#zagolovki)
- [Тело запроса (JSON)](ru/api-requests/chat-create#telo-zaprosa-json)
- [Ограничения](ru/api-requests/chat-create#ogranicheniya)
- [Результат](ru/api-requests/chat-create#rezultat)
- [Пример запроса](ru/api-requests/chat-create#primer-zaprosa)
- [Пример успешного ответа](ru/api-requests/chat-create#primer-uspeshnogo-otveta)
- [Пример ответа с ошибкой](ru/api-requests/chat-create#primer-otveta-s-oshibkoj)

Метод позволяет создавать чат или канал, добавлять его описание и иконку, назначать администраторов, добавлять участников (для чата) или подписчиков (для канала).

HTTP метод: `POST`

URL: `https://botapi.messenger.yandex.net/bot/v1/chats/create/`

## Заголовки

```
Authorization: OAuth <токен>
Content-Type: application/json
```

## Тело запроса (JSON)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `name` | Да | `string` | Название чата (канала) | Не более 200 символов |
| `description` | Да | `string` | Описание чата (канала) | Не более 500 символов, допустима пустая строка |
| `avatar_url` | Нет | `string` | Иконка чата (канала) | URL изображения |
| `admins` | Нет | `User``[]` | Список администраторов чата (канала) | Не более 100 пользователей за раз |
| `members` | Нет | `User``[]` | Список участников чата | Список должен быть пустым, если создается канал вместо чата (`channel=true`)   Не более 500 пользователей за раз |
| `channel` | Нет | `boolean` | Флаг для создания канала вместо чата | — |
| `subscribers` | Нет | `User``[]` | Список подписчиков канала | Список должен быть пустым, если создается чат (`channel=false`)   Не более 500 пользователей за раз |

## Ограничения

1. Бот может создавать чат (канал) только с участниками организации, которой он принадлежит.
2. Все создаваемые чаты (каналы) принадлежат организации, которой принадлежит бот.
3. Бот становится админстратором созданного чата (канала).
4. Бот не может добавить в чат участника, для которого это запрещено настройками приватности.

## Результат

Результатом успешного запроса является ответ с кодом 200 и телом с JSON, где содержится информация о созданном чате (канале).

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `chat_id` | Да | `string` | ID созданного чата (канала) |

В случае ошибки возвращается соответствующий статус HTTP. Описание ошибки приходит в поле `description`.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `description` | Да | `string` | Описание ошибки |

## Пример запроса

```
curl -H 'Authorization: OAuth AtXXXXXXXXXXX' -H "Content-Type: application/json" -d '{"name": "Поздравляем Аню", "description": "Чат в честь дня рождения","members": [{"login": "anya@example.org"}, {"login": "masha@example.org"}, {"login": "petya@example.org"}]}' 'https://botapi.messenger.yandex.net/bot/v1/chats/create/'
```

## Пример успешного ответа

```
{"ok": true, "chat_id": "0/0/4f24b544-697c-4e18-a9c1-b39432ee9bf9"}
```

## Пример ответа с ошибкой

```
{"ok": false, "description": "Creating chat with user restricted by privacy settings"}
```


---

# Управление участниками чата или канала

- [Заголовки](ru/api-requests/chat-members#zagolovki)
- [Тело запроса (JSON)](ru/api-requests/chat-members#telo-zaprosa-json)
- [Ограничения](ru/api-requests/chat-members#ogranicheniya)
- [Результат](ru/api-requests/chat-members#rezultat)
- [Пример успешного ответа](ru/api-requests/chat-members#primer-uspeshnogo-otveta)
- [Пример ответа с ошибкой](ru/api-requests/chat-members#primer-otveta-s-oshibkoj)

Метод позволяет добавлять и удалять участников в чат, добавлять и удалять подписчиков канала, а также назначать администраторов чата или канала.

HTTP метод: `POST`

URL: `https://botapi.messenger.yandex.net/bot/v1/chats/updateMembers/`

## Заголовки

```
Authorization: OAuth <токен>
Content-Type: application/json
```

## Тело запроса (JSON)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `chat_id` | Да | `string` | ID чата (канала) | Бот должен состоять в чате (канале) |
| `members` | Нет\* | `User``[]` | Список пользователей, которых нужно сделать участниками чата | Бот должен состоять в чате. Если хотя бы один из пользователей (`User`) был администратором, бот должен быть администратором   Не более 500 пользователей за раз |
| `admins` | Нет\* | `User``[]` | Список пользователей, которых нужно сделать администраторами чата (канала) | Бот должен быть администратором чата (канала)   Не более 100 пользователей за раз |
| `subscribers` | Нет\* | `User``[]` | Список пользователей, которых нужно сделать подписчиками канала | Бот должен состоять в чате. Пользователи (`User`) не могут быть администраторами чата   Не более 500 пользователей за раз |
| `remove` | Нет\* | `User``[]` | Список пользователей, которых нужно удалить из чата (канала) | Для удаления администраторов бот должен быть администратором чата (канала)   Не более 500 пользователей за раз |

(\*) Параметры `members`, `admins`, `subscribers` и `remove` являются необязательными, но должен быть задан хотя бы один из списков.

## Ограничения

Каждый пользователь в запросе должен быть уникален, в противном случае будет возвращена ошибка.

## Результат

В случае успешного запроса все пользователи будут иметь указанные в запросе роли. В случае ошибки будет возвращено сообщение с ее описанием, роли пользователей не поменяются.

## Пример успешного ответа

```
{"ok": true}
```

## Пример ответа с ошибкой

```
{"ok": false, "description": "Bot is not a member of the chat"}
```



---

# Получение ссылок на пользователя

- [Заголовки](ru/api-requests/get-user-link#zagolovki)
- [Тело запроса (JSON)](ru/api-requests/get-user-link#telo-zaprosa-json)
- [Ограничения](ru/api-requests/get-user-link#ogranicheniya)
- [Результат](ru/api-requests/get-user-link#rezultat)
- [Пример запроса](ru/api-requests/get-user-link#primer-zaprosa)
- [Пример успешного ответа](ru/api-requests/get-user-link#primer-uspeshnogo-otveta)
- [Пример ответа с ошибкой](ru/api-requests/get-user-link#primer-otveta-s-oshibkoj)

Метод позволяет получить ссылки, по которым можно открыть диалог (приватный чат) с пользователем или позвонить ему.

HTTP метод: `GET`

URL: `https://botapi.messenger.yandex.net/bot/v1/users/getUserLink/`

## Заголовки

```
Authorization: OAuth <токен>
Content-Type: application/json
```

## Тело запроса (JSON)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `login` | Да | `string` | Логин пользователя | — |

## Ограничения

Бот может возвращать ссылки только на пользователей из организации, в которой состоят и он, и пользователь, по которому запрашивается информация.

## Результат

Результатом успешного запроса является ответ с кодом 200 и телом с JSON, в котором содержится информация о ссылках на пользователя.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `id` | Да | `string` | ID пользователя в мессенджере |
| `chat_link` | Да | `string` | Ссылка на чат с пользователем |
| `call_link` | Да | `string` | Ссылка на звонок пользователю |

В случае ошибки возвращается соответствующий статус HTTP. Описание ошибки приходит в поле `description`.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `description` | Да | `string` | Описание ошибки |

## Пример запроса

```
curl -X GET -H 'Authorization: OAuth AtXXXXXXXXXXX' -H "Content-Type: application/json" 'https://botapi.messenger.yandex.net/bot/v1/users/getUserLink?login=userlogin'
```

## Пример успешного ответа

```
{"ok": true, "id": "someuserid", "chat_link": "https://yandex.ru/chat#/user/someuserid", "call_link": "messenger://call/create/private?user_id=someuserid"}
```

## Пример ответа с ошибкой

```
{"ok": false, "description": "User not found"}
```



---

# Отправка текстового сообщения

- [Заголовки](ru/api-requests/message-send-text#zagolovki)
- [Тело запроса (JSON)](ru/api-requests/message-send-text#telo-zaprosa-json)
- [Ограничения](ru/api-requests/message-send-text#restriction)
- [Результат](ru/api-requests/message-send-text#result)
- [Пример запроса](ru/api-requests/message-send-text#primer-zaprosa)
- [Пример успешного ответа](ru/api-requests/message-send-text#primer-uspeshnogo-otveta)
- [Пример ответа с ошибкой](ru/api-requests/message-send-text#primer-otveta-s-oshibkoj)

Метод позволяет создавать текстовые сообщения, настраивать их параметры и отправлять в чат. Для каждого сообщения можно указать, помечается ли оно важным, является ли ответом на другое сообщение или входит в состав треда, нужно ли отключить уведомление для сообщения или запретить открытие ссылок, а также необходимо ли вместе с сообщением формировать инлайн-кнопки для быстрых ответов.

HTTP метод: `POST`

URL: `https://botapi.messenger.yandex.net/bot/v1/messages/sendText/`

## Заголовки

```
Authorization: OAuth <токен>
Content-Type: application/json
```

## Тело запроса (JSON)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `chat_id` | Нет\* | `string` | ID группового чата | Бот должен быть участником чата |
| `login` | Нет\* | `string` | Логин пользователя | — |
| `text` | Да | `string` | Текст сообщения | Не более 6000 символов |
| `payload_id` | Нет | `string` | ID запроса | ID должен быть уникальным для каждого запроса. Запросы с одинаковым ID трактуются как дубликаты |
| `reply_message_id` | Нет | `integer` | ID сообщения, на которое будет ответ | Сообщение должно быть из того же чата |
| `disable_notification` | Нет | `boolean` | Нужно ли отключить уведомление | Значение по умолчанию: `false` |
| `important` | Нет | `boolean` | Является ли сообщение важным | Значение по умолчанию: `false` |
| `disable_web_page_preview` | Нет | `boolean` | Отключить раскрытие ссылок в сообщении | Значение по умолчанию: `false` |
| `thread_id` | Нет | `integer` | ID сообщения, под которым будет открыт тред | — |
| `inline_keyboard` | Нет | `Button``[]` | Массив инлайн-кнопок под сообщением, с помощью котрых можно отправить быстрый ответ | Не более 100 кнопок |

(\*) Параметры `chat_id` и `login` являются необязательными, но необходимо заполнить хотя бы один из двух:

- При заполнении `chat_id` сообщение будет отправлено в групповой чат, заданный этим ID.
- При заполнении `login` сообщение будет отправлено пользователю в приватный чат.

## Ограничения

1. Бот может отправлять сообщения только в те чаты, в которых он является участником или админом.
2. Бот не может отправлять личные сообщения пользователям, для которых это запрещено настройками приватности.
3. Бот не может отправлять личные сообщения пользователям вне своей организации.

## Результат

Результатом успешного запроса является ответ с кодом 200 и телом с JSON, где содержится информация об отправленном сообщении.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `message_id` | Да | `integer` | ID сообщения в чате |

В случае ошибки возвращается соответствующий статус HTTP. Описание ошибки приходит в поле `description`.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `description` | Да | `string` | Описание ошибки |

## Пример запроса

```
curl -X POST -H 'Authorization: OAuth AtXXXXXXXXXXX' -H "Content-Type: application/json" -d '{"chat_id":"0/0/4f24b544-697c-4e18-a9c1-b39432ee9bf9", "text": "Привет!"}' 'https://botapi.messenger.yandex.net/bot/v1/messages/sendText/'
```

## Пример успешного ответа

```
{"ok": true, "message_id": 1647523230504005}
```

## Пример ответа с ошибкой

```
{"ok": false, "description": "Bot is not a member of the chat"}
```



---

# Отправка файла

- [Заголовки](ru/api-requests/message-send-file#zagolovki)
- [Тело запроса (multipart/form-data)](ru/api-requests/message-send-file#telo-zaprosa-multipart/form-data)
- [Ограничения](ru/api-requests/message-send-file#ogranicheniya)
- [Результат](ru/api-requests/message-send-file#rezultat)
- [Пример запроса](ru/api-requests/message-send-file#primer-zaprosa)
- [Пример успешного ответа](ru/api-requests/message-send-file#primer-uspeshnogo-otveta)
- [Пример ответа с ошибкой](ru/api-requests/message-send-file#primer-otveta-s-oshibkoj)

Метод позволяет отправлять файлы в приватные или групповые чаты.

HTTP метод: `POST`

URL: `https://botapi.messenger.yandex.net/bot/v1/messages/sendFile/`

## Заголовки

```
Authorization: OAuth <токен>
```

## Тело запроса (multipart/form-data)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `chat_id` | Нет\* | `string` | ID чата, в который нужно отправить файл | Бот должен состоять в чате |
| `login` | Нет\* | `string` | Логин пользователя, которому нужно отправить файл | Бот должен состоять в чате |
| `document` | Да | `binary data` | Содержимое файла | — |
| `thread_id` | Нет | `integer` | Идентификатор треда (timestamp сообщения) | — |

(\*) Параметры `chat_id` и `login` являются необязательными, но необходимо заполнить хотя бы один из двух:

- При заполнении `chat_id` файл будет отправлен в групповой чат, заданный этим ID.
- При заполнении `login` файл будет отправлен пользователю в приватный чат.

Имя загружаемого файла берется из параметра `filename` заголовка `Content-Disposition`. Также желательно правильно задать MIME-тип файла, для правильного отображения его браузером.

Например,

```
Content-Disposition: form-data; name="document"; filename="doc.jpg"
Content-Type: image/jpeg
```

## Ограничения

Ограничения аналогичны [ограничениям](ru/api-requests/message-send-text#restriction) для метода отправки текстового сообщения.

## Результат

Результат выполнения запроса аналогичен [результату](ru/api-requests/message-send-text#result) для метода отправки текстового сообщения.

## Пример запроса

```
curl -H 'Authorization: OAuth AtXXXXXXXXXXX' -F 'login=vasya@example.org' -F 'document=@report.pdf' 'https://botapi.messenger.yandex.net/bot/v1/messages/sendFile'
```

## Пример успешного ответа

```
{"ok": true, "message_id": 1647523230504005}
```

## Пример ответа с ошибкой

```
{"ok": false, "description": "Bot is not a member of the chat"}
```



---

# Получение файла

- [Заголовки](ru/api-requests/message-get-file#zagolovki)
- [Тело запроса](ru/api-requests/message-get-file#telo-zaprosa)
- [Результат](ru/api-requests/message-get-file#rezultat)
- [Пример запроса](ru/api-requests/message-get-file#primer-zaprosa)
- [Пример ответа с ошибкой](ru/api-requests/message-get-file#primer-otveta-s-oshibkoj)

Метод позволяет получать файлы, которые были отправлены в чаты.

HTTP метод: `GET` или `POST`

URL: `https://botapi.messenger.yandex.net/bot/v1/messages/getFile/`

## Заголовки

```
Authorization: OAuth <токен>
Content-Type: application/json (только для POST-запросов)
```

## Тело запроса

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `file_id` | Да | `string` | ID файла | — |

## Результат

В результате успешного запроса будет открыт поток для отправки запрошенного файла.

## Пример запроса

```
curl -H 'Authorization: OAuth AtXXXXXXXXXXX' \
     -F file_id='disk/<guid>' \
     'https://botapi.messenger.yandex.net/bot/v1/messages/getFile'
```

## Пример ответа с ошибкой

```
{
  "ok": false,
  "description": "Failed to get file"
}
```



---

# Отправка изображения

- [Заголовки](ru/api-requests/message-send-image#zagolovki)
- [Тело запроса (multipart/form-data)](ru/api-requests/message-send-image#telo-zaprosa-multipart/form-data)
- [Пример запроса](ru/api-requests/message-send-image#primer-zaprosa)
- [Пример успешного ответа](ru/api-requests/message-send-image#primer-uspeshnogo-otveta)
- [Пример ответа с ошибкой](ru/api-requests/message-send-image#primer-otveta-s-oshibkoj)

Метод позволяет отправлять изображения в приватные или групповые чаты.

HTTP метод: `POST`

URL: `https://botapi.messenger.yandex.net/bot/v1/messages/sendImage/`

## Заголовки

```
Authorization: OAuth <токен>
```

## Тело запроса (multipart/form-data)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `chat_id` | Нет\* | `string` | ID чата, в который нужно отправить изображение | Бот должен состоять в чате |
| `login` | Нет\* | `string` | Логин пользователя, которому нужно отправить изображение | Бот должен состоять в чате |
| `image` | Да | `binary data` | Содержимое файла с изображением | — |
| `thread_id` | Нет | `integer` | Идентификатор треда (timestamp сообщения) | — |

(\*) Параметры `chat_id` и `login` являются необязательными, но необходимо заполнить хотя бы один из двух:

- При заполнении `chat_id` изображение будет отправлено в групповой чат, заданный этим ID.
- При заполнении `login` изображение будет отправлено пользователю в приватный чат.

Отправка изображения аналогична [отправке файла](ru/api-requests/message-send-file).

## Пример запроса

```
curl -H 'Authorization: OAuth AtXXXXXXXXXXX' -F 'login=vasya@example.org' -F 'image=@report.pdf' 'https://botapi.messenger.yandex.net/bot/v1/messages/sendImage'
```

## Пример успешного ответа

```
{"ok": true, "message_id": 1647523230504005}
```

## Пример ответа с ошибкой

```
{"ok": false, "description": "Bot is not a member of the chat"}
```



---

# Отправка альбома

- [Заголовки](ru/api-requests/message-send-gallery#zagolovki)
- [Тело запроса (multipart/form-data)](ru/api-requests/message-send-gallery#telo-zaprosa-multipart/form-data)
- [Пример запроса](ru/api-requests/message-send-gallery#primer-zaprosa)
- [Пример успешного ответа](ru/api-requests/message-send-gallery#primer-uspeshnogo-otveta)
- [Пример ответа с ошибкой](ru/api-requests/message-send-gallery#primer-otveta-s-oshibkoj)

Метод позволяет отправлять альбомы в приватные или групповые чаты.

HTTP метод: `POST`

URL: `https://botapi.messenger.yandex.net/bot/v1/messages/sendGallery/`

## Заголовки

```
Authorization: OAuth <токен>
```

## Тело запроса (multipart/form-data)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `chat_id` | Нет\* | `string` | ID чата, в который нужно отправить альбом | Бот должен состоять в чате |
| `login` | Нет\* | `string` | Логин пользователя, которому нужно отправить альбом | Бот должен состоять в чате |
| `images` | Да | `binary data` | Содержимое файлов с изображениями | — |
| `thread_id` | Нет | `integer` | Идентификатор треда (timestamp сообщения) | — |

(\*) Параметры `chat_id` и `login` являются необязательными, но необходимо заполнить хотя бы один из двух:

- При заполнении `chat_id` альбом будет отправлено в групповой чат, заданный этим ID.
- При заполнении `login` альбом будет отправлено пользователю в приватный чат.

Отправка альбома аналогична [отправке изображения](ru/api-requests/message-send-image).

## Пример запроса

```
curl -H 'Authorization: OAuth AtXXXXXXXXXXX' -F 'login=vasya@example.org' -F 'images=@cat1.jpg' -F 'images=@cat2.png' 'https://botapi.messenger.yandex.net/bot/v1/messages/sendGallery'
```

## Пример успешного ответа

```
{"ok": true, "message_id": 1647523230504005}
```

## Пример ответа с ошибкой

```
{"ok": false, "description": "Bot is not a member of the chat"}
```



---

# Удаление сообщения

- [Заголовки](ru/api-requests/message-delete#zagolovki)
- [Тело запроса (JSON)](ru/api-requests/message-delete#telo-zaprosa-json)
- [Результат](ru/api-requests/message-delete#rezultat)
- [Пример запроса](ru/api-requests/message-delete#primer-zaprosa)
- [Пример успешного ответа](ru/api-requests/message-delete#primer-uspeshnogo-otveta)
- [Пример ответа с ошибкой](ru/api-requests/message-delete#primer-otveta-s-oshibkoj)

Метод позволяет удалять сообщения из чатов.

HTTP метод: `POST`

URL: `https://botapi.messenger.yandex.net/bot/v1/messages/delete/`

## Заголовки

```
Authorization: OAuth <токен>
Content-Type: application/json
```

## Тело запроса (JSON)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `chat_id` | Нет\* | `string` | ID группового чата | Бот должен быть участником чата |
| `login` | Нет\* | `string` | Логин пользователя | — |
| `message_id` | Да | `integer` | ID сообщения, которое надо удалить | Сообщение должно быть из того же чата |
| `thread_id` | Нет | `integer` | Идентификатор треда (timestamp сообщения) | — |

(\*) Параметры `chat_id` и `login` являются необязательными, но необходимо заполнить хотя бы один из двух.

## Результат

Результатом успешного запроса является ответ с кодом 200 и телом с JSON, где содержится идентификатор удалённого сообщения.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `message_id` | Да | `integer` | ID удалённого сообщения |

В случае ошибки возвращается соответствующий статус HTTP. Описание ошибки приходит в поле `description`.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `description` | Да | `string` | Описание ошибки |

## Пример запроса

```
curl -X POST -H 'Authorization: OAuth AtXXXXXXXXXXX' -H "Content-Type: application/json" -d '{"chat_id":"0/0/4f24b544-697c-4e18-a9c1-b39432ee9bf9", "message_id": 1695644763694005}' 'https://botapi.messenger.yandex.net/bot/v1/messages/delete/'
```

## Пример успешного ответа

```
{"ok": true, "message_id": 1695644763694005}
```

## Пример ответа с ошибкой

```
{"ok": false, "description": "Bot is not a member of the chat"}
```



---

# Создание опроса

- [Заголовки](ru/api-requests/poll-create#zagolovki)
- [Тело запроса (JSON)](ru/api-requests/poll-create#telo-zaprosa-json)
- [Ограничения](ru/api-requests/poll-create#ogranicheniya)
- [Результат](ru/api-requests/poll-create#rezultat)
- [Пример запроса](ru/api-requests/poll-create#primer-zaprosa)
- [Пример успешного ответа](ru/api-requests/poll-create#primer-uspeshnogo-otveta)
- [Пример ответа с ошибкой](ru/api-requests/poll-create#primer-otveta-s-oshibkoj)

Метод позволяет создавать опросы.

HTTP метод: `POST`

URL: `https://botapi.messenger.yandex.net/bot/v1/messages/createPoll/`

## Заголовки

```
Authorization: OAuth <токен>
Content-Type: application/json
```

## Тело запроса (JSON)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `chat_id` | Нет\* | `string` | ID группового чата | Бот должен быть участником чата |
| `login` | Нет\* | `string` | Логин пользователя | — |
| `title` | Да | `string` | Заголовок опроса | — |
| `answers` | Да | `array of string` | Варианты ответа для опроса | В списке должно быть не менее двух и не более ста элементов |
| `max_choices` | Нет | `integer` | Максимальное количество возможных ответов | Положительное число. Значение по умолчанию: `1` |
| `is_anonymous` | Нет | `boolean` | Является ли опрос анонимным | Значение по умолчанию: `false` |
| `payload_id` | Нет | `string` | ID запроса | ID должен быть уникальным для каждого запроса. Запросы с одинаковым ID трактуются как дубликаты |
| `reply_message_id` | Нет | `integer` | ID сообщения, на которое будет ответ | Сообщение должно быть из того же чата |
| `disable_notification` | Нет | `boolean` | Нужно ли отключить уведомление | Значение по умолчанию: `false` |
| `important` | Нет | `boolean` | Является ли сообщение важным | Значение по умолчанию: `false` |
| `disable_web_page_preview` | Нет | `boolean` | Отключить раскрытие ссылок в сообщении | Значение по умолчанию: `false` |
| `thread_id` | Нет | `integer` | Идентификатор треда (timestamp сообщения) | — |

(\*) Параметры `chat_id` и `login` являются необязательными, но необходимо заполнить хотя бы один из двух:

- При заполнении `chat_id` сообщение с опросом будет отправлено в групповой чат, заданный этим ID.
- При заполнении `login` сообщение с опросом будет отправлено пользователю в приватный чат.

## Ограничения

1. Бот может отправлять сообщения только в те чаты, в которых он является участником или админом.
2. Бот не может отправлять личные сообщения пользователям, для которых это запрещено настройками приватности.
3. Бот не может отправлять личные сообщения пользователям вне своей организации.

## Результат

Результатом успешного запроса является ответ с кодом 200 и телом с JSON, где содержится информация об отправленном сообщении с опросом.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `message_id` | Да | `integer` | ID сообщения с опросом в чате |

В случае ошибки возвращается соответствующий статус HTTP. Описание ошибки приходит в поле `description`.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `description` | Да | `string` | Описание ошибки |

## Пример запроса

```
curl -X POST -H 'Authorization: OAuth AtXXXXXXXXXXX' -H "Content-Type: application/json" -d '{"chat_id":"0/0/4f24b544-697c-4e18-a9c1-b39432ee9bf9", "title": "Вам нравится этот опрос?", "answers": ["Да!", "Не очень"], "is_anonymous": "true"}' 'https://botapi.messenger.yandex.net/bot/v1/messages/createPoll/'
```

## Пример успешного ответа

```
{"ok": true, "message_id": 1647523230504005}
```

## Пример ответа с ошибкой

```
{"ok": false, "description": "answers: ["Ensure this field has at least 2 elements."]"}
```



---

# Получение результатов опроса

- [Заголовки](ru/api-requests/poll-get-results#zagolovki)
- [Тело запроса (JSON или URL Query)](ru/api-requests/poll-get-results#telo-zaprosa-json-ili-url-query)
- [Результат](ru/api-requests/poll-get-results#rezultat)
- [Пример запроса](ru/api-requests/poll-get-results#primer-zaprosa)
- [Пример успешного ответа](ru/api-requests/poll-get-results#primer-uspeshnogo-otveta)
- [Пример ответа с ошибкой](ru/api-requests/poll-get-results#primer-otveta-s-oshibkoj)

Метод позволяет получать результаты опроса пользователей в чате: общее количество проголосовавших и число голосов, отданных за каждый вариант ответа.

HTTP метод: `GET`

URL: `https://botapi.messenger.yandex.net/bot/v1/polls/getResults/`

## Заголовки

```
Authorization: OAuth <токен>
Content-Type: application/json
```

## Тело запроса (JSON или URL Query)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `chat_id` | Нет\* | `string` | ID группового чата | Бот должен быть участником чата |
| `login` | Нет\* | `string` | Логин пользователя | — |
| `message_id` | Да | `integer` | ID сообщения с опросом в чате | — |
| `invite_hash` | Нет | `string` | Хеш пригласительной ссылки, если бот еще не состоит в чате | — |
| `thread_id` | Нет | `integer` | Идентификатор треда (timestamp сообщения) | — |

(\*) Параметры `chat_id` и `login` являются необязательными, но необходимо заполнить хотя бы один из двух.

## Результат

Результатом успешного запроса является ответ с кодом 200 и телом с JSON, где содержится информация о результатах опроса.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `answers` | Да | `map from int to int` | Результаты опроса, в формате ключ - номер варианта, значение - количество голосов |
| `voted_count` | Да | `integer` | Количество проголосовавших в опросе |

## Пример запроса

```
curl -H 'Authorization: OAuth AtXXXXXXXXXXX' 'https://botapi.messenger.yandex.net/bot/v1/polls/getResults?login=maria&message_id=1647523230504005'
```

## Пример успешного ответа

```
{"ok": true, "voted_count": 5, "answers": {'1': 5, '2': 0}}
```

## Пример ответа с ошибкой

```
{"ok": false, "description": "Bot is not a member of the chat"}
```



---

# Получение списка проголосовавших участников опроса

- [Заголовки](ru/api-requests/poll-get-voters#zagolovki)
- [Тело запроса (JSON или URL Query)](ru/api-requests/poll-get-voters#telo-zaprosa-json-ili-url-query)
- [Схема работы](ru/api-requests/poll-get-voters#shema-raboty)
- [Результат](ru/api-requests/poll-get-voters#rezultat)
- [Пример запроса](ru/api-requests/poll-get-voters#primer-zaprosa)
- [Пример успешного ответа](ru/api-requests/poll-get-voters#primer-uspeshnogo-otveta)
- [Пример ответа с ошибкой](ru/api-requests/poll-get-voters#primer-otveta-s-oshibkoj)

Метод позволяет получить количество и список участников опроса, которые проголосовали за определенный вариант ответа.

HTTP метод: `GET`

URL: `https://botapi.messenger.yandex.net/bot/v1/polls/getVoters/`

## Заголовки

```
Authorization: OAuth <токен>
Content-Type: application/json
```

## Тело запроса (JSON или URL Query)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `chat_id` | Нет\* | `string` | ID группового чата | Бот должен быть участником чата |
| `login` | Нет\* | `string` | Логин пользователя | — |
| `message_id` | Да | `integer` | ID сообщения с опросом в чате | — |
| `invite_hash` | Нет | `string` | Хеш пригласительной ссылки, если бот еще не состоит в чате | — |
| `limit` | Нет | `integer` | Максимальное количество проголосовавших, которое будет получено в ответе на запрос | Не более `1000`. Значение по умолчанию: `100` |
| `cursor` | Нет | `integer` | ID голоса, начиная с которого будет сформирован список проголосовавших | Положительное число. При значении `0` (значение по умолчанию) возвращается список из последних проголосовавших в опросе |
| `answer_id` | Да | `integer` | Номер варианта ответа, по которому запрашиваются проголосовавшие | — |
| `thread_id` | Нет | `integer` | Идентификатор треда (timestamp сообщения) | — |

(\*) Параметры `chat_id` и `login` являются необязательными, но необходимо заполнить хотя бы один из двух.

## Схема работы

Запрос на получение проголосовавших в опросе формируется для конкретного варианта ответа с номером `answer_id`.

Список проголосовавших возвращается частями, начиная с последнего проголосовавшего пользователя. Каждая часть списка направляется в ответе на отдельный запрос. Максимальное количество пользователей в каждой части равно значению параметра `limit` запроса.

Для получения первой части списка значение параметра `cursor` запроса должно быть равно `0`. Чтобы получить очередную часть, в параметре `cursor` нового запроса необходимо указать значение параметра `cursor`, полученное в ответе на предыдущий запрос. Если уже передана вся информация о проголосовавших за вариант, в ответе на следующий подобный запрос придет пустой список.

## Результат

Результатом успешного запроса является ответ с кодом 200 и телом с JSON, где содержится список проголосовавших

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `answer_id` | Да | `integer` | Номер варианта ответа для которого получен результат |
| `voted_count` | Да | `integer` | Количество проголосовавших в опросе |
| `cursor` | Да | `integer` | ID последнего полученного голоса |
| `votes` | Да | `Vote``[]` | Полученные голоса в опросе |

## Пример запроса

```
curl -H 'Authorization: OAuth AtXXXXXXXXXXX' 'https://botapi.messenger.yandex.net/bot/v1/polls/getVoters?chat_id=0/0/4f24b544-697c-4e18-a9c1-b39432ee9bf9&message_id=1647523230504005&answer=1&limit=3'
```

## Пример успешного ответа

```
{"ok": true, "voted_count": 3, "cursor": 3912830489212,  "votes": [{"timestamp": 382981920210, "user":{"login": "anya@example.org"}}, {"timestamp": 382981920123, "user":{"login": "masha@example.org"}}, {"timestamp": 38298192089213, "user":{"login": "petya@example.org"}}]}
```

## Пример ответа с ошибкой

```
{"ok": false, "description": "Bot is not a member of the chat"}
```



---

# Получение обновлений

При запросе обновлений бот получит все новые сообщения из чатов, где он является подписчиком, участником или администратором. Если бот покидает чат, он может получить обновления, которые были сделаны до его выхода.

Бот может получать обновления двумя способами:

- Через [вебхук](ru/api-requests/update-webhook) (webhook) — если боту добавить вебхук (настройка `webhook_url`), то все обновления будут отправляться в виде POST-запроса по указанному адресу. Задать вебхук можно как в [интерфейсе](https://yandex.ru/support/business/bot-platform.html#bot-settings) Яндекс 360 для бизнеса, так и через [API](ru/api-requests/update-webhook#set_webhook_url). Чтобы обновления больше не поступали этим способом, удалите адрес в настройках бота или сбросьте вебхук с помощью [запроса](ru/api-requests/update-webhook#reset_webhook_url).
- Через [опрос сервера](ru/api-requests/update-polling) (polling) — обращаясь к `bot/v1/messages/getUpdates/`, можно получить информацию обо всех сообщениях, которые были доставлены боту с момента последнего обновления.

Одновременно эти способы использовать нельзя: после установки `webhook_url` метод `bot/v1/messages/getUpdates/` перестанет отдавать новые сообщения.

Примечание

Способ получения обновлений через вебхук генерирует меньше трафика. Удобнее настраивать вебхук в интерфейсе.



---

# Получение обновлений: polling

- [Заголовки](ru/api-requests/update-polling#zagolovki)
- [Тело запроса (JSON или URL Query)](ru/api-requests/update-polling#telo-zaprosa-json-ili-url-query)
- [Схема работы](ru/api-requests/update-polling#shema-raboty)
- [Результат](ru/api-requests/update-polling#rezultat)
- [Пример запроса (GET)](ru/api-requests/update-polling#primer-zaprosa-get)
- [Пример запроса (POST)](ru/api-requests/update-polling#primer-zaprosa-post)
- [Примеры успешных ответов](ru/api-requests/update-polling#responses)
  - [Прием сообщения в приватный чат](ru/api-requests/update-polling#priem-soobsheniya-v-privatnyj-chat)
  - [Прием сообщения в групповой чат](ru/api-requests/update-polling#priem-soobsheniya-v-gruppovoj-chat)
  - [Прием сообщения в канал](ru/api-requests/update-polling#priem-soobsheniya-v-kanal)
  - [Прием пересланного сообщения в приватный чат](ru/api-requests/update-polling#priem-pereslannogo-soobsheniya-v-privatnyj-chat)
  - [Прием стикера](ru/api-requests/update-polling#priem-stikera)
  - [Прием картинки](ru/api-requests/update-polling#priem-kartinki)
  - [Прием галереи](ru/api-requests/update-polling#priem-galerei)
  - [Прием файла](ru/api-requests/update-polling#priem-fajla)
- [Пример ответа с ошибкой](ru/api-requests/update-polling#primer-otveta-s-oshibkoj)

Метод позволяет получить информацию обо всех сообщениях, которые были доставлены боту с момента последнего обновления.

HTTP метод: `GET` или `POST`

URL: `https://botapi.messenger.yandex.net/bot/v1/messages/getUpdates/`

## Заголовки

```
Authorization: OAuth <токен>
Content-Type: application/json (только для POST-запросов)
```

## Тело запроса (JSON или URL Query)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `limit` | Нет | `integer` | Максимальное количество обновлений в ответе | Не более `1000`. Значение по умолчанию: `100` |
| `offset` | Нет | `integer` | ID первого запрашиваемого обновления | Положительное число. Значение по умолчанию: `0` |

## Схема работы

Работа с `getUpdates` начинается с запроса со значением `limit`, равным желаемому количеству сообщений в ответе, и значением `offset`, равным 0. Такой запрос вернет в ответе самые первые из доступных боту обновлений. После обработки ответа запрос следующей пачки обновлений необходимо сделать с `offset`, равным `max(updates.update_id) + 1`.

Запрос `getUpdates` стирает все обновления с `update_id < offset`, делая их недоступными для получения ботом.

Бот получает все сообщения из чатов, где он является подписчиком, участником или администратором. Если бот покидает чат, он может получить обновления, которые были сделаны до его выхода.

## Результат

Результатом успешного запроса является ответ с кодом 200 и телом с JSON, где содержится информация обо всех сообщениях, которые были доставлены боту с момента последнего обновления.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `updates` | Да | `Update``[]` | Полученные сообщения |

В случае ошибки возвращается соответствующий статус HTTP. Описание ошибки приходит в поле `description`.

| Имя параметра | Обязательный | Тип | Описание |
| --- | --- | --- | --- |
| `ok` | Да | `boolean` | Флаг успешности выполнения |
| `description` | Да | `string` | Описание ошибки |

## Пример запроса (GET)

```
curl -H 'Authorization: OAuth AtXXXXXXXXXXX' \
    'https://botapi.messenger.yandex.net/bot/v1/messages/getUpdates?limit=1&offset=1569302'
```

## Пример запроса (POST)

```
curl -H 'Authorization: OAuth AtXXXXXXXXXXX' \
     -H "Content-Type: application/json" \
     -d '{"limit": 1, "offset": 1569302}' \
     'https://botapi.messenger.yandex.net/bot/v1/messages/getUpdates/'
```

## Примеры успешных ответов

Каждый пример является ответом на запрос:

```
curl https://botapi.messenger.yandex.net/bot/v1/messages/getUpdates/ \
    -H "Authorization: OAuth AXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

### Прием сообщения в приватный чат

```
{
  "updates": [
    {
      "message_id": 1702323240544005,
      "timestamp": 1702323240,
      "chat": {
        "type": "private"
      },
      "from": {
        "id": "<guid>",
        "display_name": "Ivan Ivanov",
        "login": "ivan_ivanov",
        "robot": false
      },
      "update_id": 1571239,
      "text": "Oh hi Mark"
    }
  ],
  "ok": true
}
```

### Прием сообщения в групповой чат

```
{
  "updates": [
    {
      "message_id": 1702325004369005,
      "timestamp": 1702325004,
      "chat": {
        "type": "group",
        "id": "0/0/<chat_guid>"
      },
      "from": {
        "id": "<guid>",
        "display_name": "Ivan Ivanov",
        "login": "ivan_ivanov",
        "robot": false
      },
      "update_id": 1571241,
      "text": "Howdy"
    }
  ],
  "ok": true
}
```

### Прием сообщения в канал

```
{
  "updates": [
    {
      "message_id": 1702332164147004,
      "timestamp": 1702332164,
      "chat": {
        "type": "channel",
        "id": "1/0/<guid>"
      },
      "from": {
        "id": "<guid>"
      },
      "update_id": 1571269,
      "text": "Probably something important"
    }
  ],
  "ok": true
}
```

### Прием пересланного сообщения в приватный чат

```
{
  "updates": [
    {
      "message_id": 1702329071098005,
      "timestamp": 1702329071,
      "chat": {
        "type": "private"
      },
      "from": {
        "id": "<guid>",
        "display_name": "Ivan Ivanov",
        "login": "ivan_ivanov",
        "robot": false
      },
      "update_id": 1571249,
      "forwarded_messages": [
        {
          "message_id": 1702323240544005,
          "timestamp": 1702323240,
          "chat": {
            "type": "private"
          },
          "from": {
            "id": "<guid2>",
            "display_name": "Petr Petrov",
            "login": "petr_petrov",
            "robot": false
          },
          "text": "Something idk"
        }
      ]
    }
  ],
  "ok": true
}
```

### Прием стикера

```
{
  "updates": [
    {
      "message_id": 1702328871591005,
      "timestamp": 1702328871,
      "chat": {
        "type": "private"
      },
      "from": {
        "id": "<guid>",
        "display_name": "Ivan Ivanov",
        "login": "ivan_ivanov",
        "robot": false
      },
      "update_id": 1571247,
      "sticker": {
        "id": "stickers/images/43/630.png",
        "set_id": "43"
      }
    }
  ],
  "ok": true
}
```

### Прием картинки

*Замечание*: для скачивания файла необходимо воспользоваться
[методом `/bot/v1/messages/getFile`](ru/api-requests/message-get-file).

```
{
  "updates": [
    {
      "message_id": 1702329451492005,
      "timestamp": 1702329451,
      "chat": {
        "type": "private"
      },
      "from": {
        "id": "<guid>",
        "display_name": "Ivan Ivanov",
        "login": "ivan_ivanov",
        "robot": false
      },
      "update_id": 1571251,
      "images": [
        [
          {
            "file_id": "disk/<guid>?size=small",
            "width": 150,
            "height": 11
          },
          {
            "file_id": "disk/<guid>?size=middle",
            "width": 250,
            "height": 18
          },
          {
            "file_id": "disk/<guid>?size=middle-400",
            "width": 400,
            "height": 29
          },
          {
            "file_id": "disk/<guid>",
            "width": 1048,
            "height": 78,
            "size": 20362,
            "name": "file.jpeg"
          }
        ]
      ]
    }
  ],
  "ok": true
}
```

### Прием галереи

*Замечание*: для скачивания файла необходимо воспользоваться
[методом `/bot/v1/messages/getFile`](ru/api-requests/message-get-file).

```
{
  "updates": [
    {
      "message_id": 1702330642781005,
      "timestamp": 1702330642,
      "chat": {
        "type": "private"
      },
      "from": {
        "id": "<guid>",
        "display_name": "Ivan Ivanov",
        "login": "ivan_ivanov",
        "robot": false
      },
      "update_id": 1571257,
      "images": [
        [
          {
            "file_id": "disk/<guid>?size=small",
            "width": 150,
            "height": 10
          },
          {
            "file_id": "disk/<guid>?size=middle",
            "width": 250,
            "height": 17
          },
          {
            "file_id": "disk/<guid>?size=middle-400",
            "width": 400,
            "height": 27
          },
          {
            "file_id": "disk/<guid>",
            "width": 868,
            "height": 60,
            "size": 21743,
            "name": "file1.jpeg"
          }
        ],
        [
          {
            "file_id": "disk/<guid>?size=small",
            "width": 150,
            "height": 11
          },
          {
            "file_id": "disk/<guid>?size=middle",
            "width": 250,
            "height": 18
          },
          {
            "file_id": "disk/<guid>?size=middle-400",
            "width": 400,
            "height": 29
          },
          {
            "file_id": "disk/<guid>",
            "width": 1048,
            "height": 78,
            "size": 20362,
            "name": "file2.jpeg"
          }
        ]
      ]
    }
  ],
  "ok": true
}
```

### Прием файла

*Замечание*: если пользователь отправил несколько файлов,
каждый из них будет представлен своим обновлением. Для скачивания каждого файла необходимо воспользоваться
[методом `/bot/v1/messages/getFile`](ru/api-requests/message-get-file).

```
{
  "updates": [
    {
      "message_id": 1702329844441005,
      "timestamp": 1702329844,
      "chat": {
        "type": "private"
      },
      "from": {
        "id": "<guid>",
        "display_name": "Ivan Ivanov",
        "login": "ivan_ivanov",
        "robot": false
      },
      "update_id": 1571253,
      "file": {
        "id": "disk/<guid>",
        "name": "data.txt",
        "size": 20
      }
    }
  ],
  "ok": true
}
```

## Пример ответа с ошибкой

```
{
  "ok": false,
  "description": "Invalid route"
}
```


---

# Получение обновлений: webhook

- [Задание webhook\_url](ru/api-requests/update-webhook#set_webhook_url)
- [Заголовки](ru/api-requests/update-webhook#zagolovki)
- [Тело запроса (JSON или URL Query)](ru/api-requests/update-webhook#telo-zaprosa-json-ili-url-query)
- [Пример запроса (POST) с установкой webhook\_url](ru/api-requests/update-webhook#primer-zaprosa-post-s-ustanovkoj-webhook_url)
- [Пример успешного ответа с установкой](ru/api-requests/update-webhook#primer-uspeshnogo-otveta-s-ustanovkoj)
- [Пример запроса (POST) со сбросом webhook\_url](ru/api-requests/update-webhook#reset_webhook_url)
- [Пример успешного ответа со сбросом](ru/api-requests/update-webhook#primer-uspeshnogo-otveta-so-sbrosom)
- [Гарантии доставки](ru/api-requests/update-webhook#garantii-dostavki)

Боту можно задать настройку `webhook_url`, после чего все обновления будут отправляться в виде POST-запроса по указанному адресу.
Тело запроса будет идентично [ответу метода `bot/v1/messages/getUpdates/`](ru/api-requests/update-polling#responses).

## Задание webhook\_url

Метод позволяет задать боту вебхук.

HTTP метод: `POST`

URL: `https://botapi.messenger.yandex.net/bot/v1/self/update/`

## Заголовки

```
Authorization: OAuth <токен>
Content-Type: application/json
```

## Тело запроса (JSON или URL Query)

| Имя параметра | Обязательный | Тип | Описание | Ограничения, значение по умолчанию |
| --- | --- | --- | --- | --- |
| `webhook_url` | Нет | `URL` | URL для получения обновлений | — |

## Пример запроса (POST) с установкой webhook\_url

```
curl -H 'Authorization: OAuth AtXXXXXXXXXXX' \
     -H "Content-Type: application/json" \
     -d '{"webhook_url": "https://my-service.ru/bot_webhook"}' \
     'https://botapi.messenger.yandex.net/bot/v1/self/update/'
```

## Пример успешного ответа с установкой

```
{
  "ok": true,
  "id": "103ecea2-e303-478d-91a7-b6d423ace527",
  "display_name": "My bot",
  "webhook_url": "https://my-service.ru/bot_webhook",
  "organizations": [567890],
  "login": "bot@my-service.ru"
}
```

## Пример запроса (POST) со сбросом webhook\_url

```
curl -H 'Authorization: OAuth AtXXXXXXXXXXX' \
     -H "Content-Type: application/json" \
     -d '{"webhook_url": null}' \
     'https://botapi.messenger.yandex.net/bot/v1/self/update/'
```

## Пример успешного ответа со сбросом

```
{
  "ok": true,
  "id": "103ecea2-e303-478d-91a7-b6d423ace527",
  "display_name": "My bot",
  "webhook_url": null,
  "organizations": [567890],
  "login": "bot@my-service.ru"
}
```

## Гарантии доставки

1. Доставка сообщений на вебхук работает по принципу "at least once" (сообщение может быть доставлено несколько раз).
2. Гарантируется порядок доставки сообщений в рамках комбинации бот + чат.
3. Если вебхук недоступен (`connection timeout = 100ms` или `read timeout = 1s` или http-код ответа `5xx`), будут осуществлены повторные попытки через интервал (интервал действует в рамках комбинации бот + чат), вычисляемый как:

   - до 8ой попытки включительно: `<время_отправки_сообщения> + <номер_текущей_попытки> * 5` (в секундах).
   - после 8ой попытки: `<время_отправки_сообщения> + <номер_текущей_попытки> * 45` (в секундах).
4. Все остальные ответы от вебхука (например статусы `2xx` или `4xx`) считаются финальными и не предусматривают повторных попыток.
5. Через 24 часа с момента отправки все недоставленные сообщения удаляются и не будут получены ботом.


---

# Используемые типы данных

- [Button](ru/data-types#button)
- [Chat](ru/data-types#chat)
- [File](ru/data-types#file)
- [Image](ru/data-types#image)
- [Sender](ru/data-types#sender)
- [Vote](ru/data-types#vote)
- [Update](ru/data-types#update)
- [User](ru/data-types#user)

## Button

Используется в запросах для описания инлайн-кнопки под текстовым сообщением.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Имя параметра** | **Обязат.** | **Тип** | **Описание** | **Ограничения** |
| `text` | Да | `string` | Текст на инлайн-кнопке | — |
| `callback_data` | Нет | `json` | Данные, которые будут отправлены на сервер при нажатии кнопки | — |

## Chat

Используется в ответах для описания чата (канала).

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Имя параметра** | **Обязат.** | **Тип** | **Описание** | **Ограничения** |
| `type` | Да | `string` | Тип чата | Возможные значения:   - `private` — приватный чат; - `group` — групповой чат; - `channel` — канал. |
| `id`\* | Нет | `string` | Идентификатор чата | У чата с типом `private` нет значимого идентификатора. В таком чате всегда два участника — бот и его собеседник. Собеседника нужно определять по объекту типа `User`, который обычно расположен рядом. |

(\*) Для группового чата (`group`) или канала (`channel`) идентификатор можно получить из адресной строки браузера:

1. Откройте чат в веб-версии Мессенджера.
2. Из адресной строки скопируйте набор символов после `https://yandex.ru/chat/#/chats/`.
3. Если браузер применяет URL-кодирование в ссылке, замените `%2F` на слэш `/`.

## File

Используется в ответах для описания файла.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Имя параметра** | **Обязат.** | **Тип** | **Описание** | **Ограничения** |
| `id` | Да | `string` | Идентификатор файла для загрузки через API | — |
| `name` | Да | `string` | Имя файла | — |
| `size` | Да | `integer` | Размер файла в байтах | — |

## Image

Используется в ответах для описания изображения.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Имя параметра** | **Обязат.** | **Тип** | **Описание** | **Ограничения** |
| `file_id` | Да | `string` | Идентификатор файла для загрузки через API | — |
| `width` | Да | `integer` | Ширина картинки | — |
| `height` | Да | `integer` | Высота картинки | — |
| `size` | Нет | `integer` | Размер файла в байтах | Указывается только для оригинала |
| `name` | Нет | `string` | Название файла (каким оно было при загрузке) | Указывается только для оригинала |

## Sender

Используется в ответах для описания отправителя сообщения.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Имя параметра** | **Обязат.** | **Тип** | **Описание** | **Ограничения** |
| `login` | Да\* | `string` | Логин пользователя, который отправил сообщение | Указывается для сообщений из чатов |
| ИЛИ `id` | Да\* | `string` | `id` канала, администратор которого отправил сообщение | Указывается для сообщений в каналах |
| `display_name` | Нет | `string` | Отображаемое имя отправителя | — |
| `robot` | Нет | `boolean` | Признак, является ли отправитель ботом | — |

(\*) В ответе придет только один из параметров `login` или `id` в зависимости от того, куда было отправлено сообщение — в чат или канал.

## Vote

Используется в ответах для описания проголосовавшего в опросе.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Имя параметра** | **Обязат.** | **Тип** | **Описание** | **Ограничения** |
| `timestamp` | Да | `integer` | ID голоса | — |
| `user` | Да | `Sender` | Проголосовавший пользователь | — |

## Update

Используется в ответах для описания сообщения в обновлении.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Имя параметра** | **Обязат.** | **Тип** | **Описание** | **Ограничения** |
| `from` | Да | `Sender` | Отправитель сообщения | — |
| `chat` | Да | `Chat` | Чат, в который было отправлено сообщение | — |
| `text` | Нет | `string` | Текст сообщения | — |
| `timestamp` | Да | `integer` | Время отправки сообщения по серверным часам: UNIX timestamp | — |
| `message_id` | Да | `integer` | Идентификатор сообщения в чате | — |
| `update_id` | Да | `integer` | Идентификатор обновления | — |
| `file` | Нет | `File` | Информация о вложенном в сообщение файле | — |
| `images` | Нет | `Image``[]` | Информация о картинках | — |

## User

Используется в запросах для описания пользователя.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Имя параметра** | **Обязат.** | **Тип** | **Описание** | **Ограничения** |
| `login`\* | Да | `string` | Логин пользователя | - Для аккаунтов на Яндексе (домен yandex.ru) логины могут использоваться без указания домена. - Для аккаунтов, созданных на других доменах, указывается полная форма логина `<login>@<domain>`. |

(\*) В качестве `login` может быть также указан адрес рассылки группы или подразделения, тогда в качестве `User` будет использоваться группа или подразделение.


---

