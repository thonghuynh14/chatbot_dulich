import time

def read_file(list_stories_path):
    lines = []
    with open(list_stories_path, "r", encoding="utf-8") as file:
        for line in file:
            lines.append(line.strip())
    return lines

def sentence_to_generator(answer):
    # Split the sentence into words
    words = answer.split()
    return words
        
def show_time_sleep_generator(message_placeholder, generator, full_response=""):
    for token in generator:
        time.sleep(0.02)
        full_response += token + " "
        message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)
    return message_placeholder, full_response

async def show_async_generator(message_placeholder, generator, full_response=""):
    async for response in generator:
        print('response: ', response)
        if response is not None:
            full_response += response
            message_placeholder.markdown(full_response +  "▌")
    return message_placeholder, full_response