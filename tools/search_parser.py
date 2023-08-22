def parse_search(query_string):
    query_iter = iter(query_string.split(" "))
    search_keywords = []
    search_options = {"level": [0, 180], "title": True, "artist": True, "mapper": True}

    while True:
        try:
            keyword = next(query_iter)

            match keyword:
                case "--level":
                    search_options["level"][0] = int(next(query_iter))
                    search_options["level"][1] = int(next(query_iter))
                case "--title-only":
                    search_options["artist"] = False
                    search_options["mapper"] = False
                case "--artist-only":
                    search_options["title"] = False
                    search_options["mapper"] = False
                case "--mapper-only":
                    search_options["title"] = False
                    search_options["artist"] = False
                case _:
                    search_keywords.append(keyword)
        except StopIteration:
            break
        except ValueError:
            return None

    return {"keywords": " ".join(search_keywords), "options": search_options}
