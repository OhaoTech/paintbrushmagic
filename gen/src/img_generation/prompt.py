import os
import dotenv
dotenv.load_dotenv("../../.env")
filename = os.getenv("PROMPT_FILENAME")
def read_prompt():
	with open('./public/'+filename, "r") as file:
		lines = file.readlines()
	lines = [line.strip() for line in lines]
	return lines




