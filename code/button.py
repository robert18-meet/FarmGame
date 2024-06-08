import pygame

class Button:
	def __init__(self, image, pos, text_input, font, base_color, hovering_color):
		self.image = image if image is not None else self.text
		self.font = font
		self.base_color, self.hovering_color = base_color, hovering_color
		self.text_input = text_input
		self.text = self.font.render(self.text_input, True, self.base_color)
		self.rect = self.image.get_rect(center=pos)
		self.text_rect = self.text.get_rect(center=pos)

	def update(self, screen):
		if self.image is not None:
			screen.blit(self.image, self.rect)
		screen.blit(self.text, self.text_rect)

	def checkForInput(self, position):
		return self.rect.collidepoint(position)

	def changeColor(self, position):
		if self.rect.collidepoint(position):
			self.text = self.font.render(self.text_input, True, self.hovering_color)
			return
		self.text = self.font.render(self.text_input, True, self.base_color)
