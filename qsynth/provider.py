from faker.providers import BaseProvider


class QsynthProviders(BaseProvider):

    def reference(self, dataset, attribute):
        return "lala"

    def random_double(self, min=0, max=1000):
        return self.generator.random.uniform(min, max)