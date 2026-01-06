from ollama import Client

is_stream = False

client = Client(
  host='http://localhost:11434',
  headers={'x-some-header': 'some-value'}
)
response = client.chat(
  model='llama3.1:latest', 
  messages=[
    {
        'role': 'user',
        'content': 'Why is the sky blue?',
    }],
    stream=is_stream
    )

if is_stream:
    for chunk in response:
        print(chunk['message']['content'], end='', flush=True)
else:
    print(response['message']['content'])
    # or access fields directly from the response object
    print(response.message.content)