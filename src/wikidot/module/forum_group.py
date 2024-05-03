from collections.abc import Iterator
from dataclasses import dataclass
import re
from typing import TYPE_CHECKING, Optional

from bs4 import BeautifulSoup

from wikidot.module.forum_category import ForumCategory, ForumCategoryCollection
from wikidot.module.forum_post import ForumPost
from wikidot.util.parser import odate as odate_parser
from wikidot.util.parser import user as user_parser

if TYPE_CHECKING:
    from wikidot.module.site import Site
    from wikidot.module.forum import Forum


class ForumGroupCollection(list["ForumGroup"]):
    def __init__(self, forum: "Forum", groups: list["ForumGroup"]):
        super().__init__(groups)
        self.forum = forum
    
    def __iter__(self) -> Iterator["ForumGroup"]:
        return super().__iter__()
    
    @staticmethod
    def get_groups(site: "Site",forum: "Forum"):
        groups = []

        response = site.amc_request([{
            "moduleName":"forum/ForumStartModule",
            "hidden":"true"
            }])[0]
        body = response.json()["body"]
        html = BeautifulSoup(body, "lxml")

        for group_info in html.select("div.forum-group"):
            group = ForumGroup(
                site=site,
                forum=forum,
                title=group_info.select_one("div.title").text,
                description=group_info.select_one("div.description").text
            )

            categories = []

            for info in group_info.select("table.table tr.head~tr"):
                name = info.select_one("td.name")
                thread_count = info.select_one("td.threads")
                post_count = info.select_one("td.posts")
                last_id = info.select_one("td.last>a").get("href")
                thread_id, post_id = re.search(r"t-(\d+).+post-(\d+)",last_id).group()

                category = ForumCategory(
                    site=site,
                    id=int(re.search(r"c-(\d+)", name.select_one("a").get("href")).group(1)),
                    description=name.select_one("div.description").text,
                    forum=forum,
                    title=name.select_one("a").text,
                    group=group,
                    threads_counts=thread_count,
                    posts_counts=post_count,
                    last=forum.thread.get(thread_id).get(post_id)
                )

                categories.append(category)
            
            group.categories = ForumCategoryCollection(site, categories)

            groups.append(group)

        forum._groups = ForumGroupCollection(site, groups)

    def find(self, title: str = None, description: str = None) -> Optional["ForumGroup"]:
        for group in self:
            if ((title is None or group.title == title) and 
                (description is None or group.description == description)):
                return group
    
    def findall(self, title: str = None, description: str = None) -> list["ForumGroup"]:
        groups = []
        for group in self:
            if ((title is None or group.title == title) and 
                (description is None or group.description == description)):
                groups.append(group)
        return groups

@dataclass
class ForumGroup:
    site: "Site"
    forum: "Forum"
    title: str
    description: str
    categories: ForumGroupCollection = None
