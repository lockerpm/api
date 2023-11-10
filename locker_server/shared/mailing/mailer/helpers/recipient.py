class Recipient:
    def __init__(self, name, address, subject, content, attachments, meta):
        self.name = name
        self.address = address
        self.subject = subject
        self.content = content
        self.attachments = attachments
        self.meta = meta
