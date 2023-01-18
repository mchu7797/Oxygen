from dataclasses import dataclass, Field


@dataclass
class SearchOption:
    level: list[int]
    title: bool = True
    artist: bool = True
    mapper: bool = True


def parse_search(query_string):
    query_iter = iter(query_string.split(" "))
    search_keywords = []
    option = SearchOption()

    while True:
        try:
            keyword = next(query_iter)

            match keyword:
                case "--level":
                    option.level = [0, 180]
                    option.level[0] = int(next(query_iter))
                    option.level[1] = int(next(query_iter))
                case "--title-only":
                    option.artist = False
                    option.mapper = False
                case "--artist-only":
                    option.title = False
                    option.mapper = False
                case "--mapper-only":
                    option.title = False
                    option.artist = False
                case _:
                    search_keywords.append(keyword)
        except StopIteration:
            break
        except ValueError:
            return None

    return {"keywords": " ".join(search_keywords), "options": option}
