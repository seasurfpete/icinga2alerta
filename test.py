import uuid

print(uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org'))
print(uuid.NAMESPACE_DNS)