from html.parser import HTMLParser
from urllib import request

import discord


class FoxParser(HTMLParser):
    """
    A helper class that overrides the base Python HTML parser.

    This is used to scrape StupidFox.net.
    """
    foxurl = None

    def handle_starttag(self, tag, attrs):
        # Only parse the 'anchor' tag.
        if tag == "a":
            # Check the list of defined attributes.
            for name, value in attrs:
                if name == "title" and value == "Random Comic":
                    # This will pull the link out of stupidfox.net
                    self.foxurl = (attrs[0][1])
                    return


def _parse_fox(html):
    """
    This function obtains a random StupidFox page from raw HTML.

    :param html: Raw StupidFox page html.
    :return: A link to a random StupidFox page.
    """
    parser = FoxParser()
    parser.feed(html)
    return parser.foxurl


async def embed_stupidfox(interaction: discord.Interaction):
    await interaction.response.defer()
    html = request.urlopen("http://stupidfox.net/168-home-sweet-home")
    foxurl = _parse_fox(str(html.read()))
    if foxurl is not None:
        # foxurl will preserve the original url of the random web page.
        imageurl = foxurl.split("/")[3]
        foxnum = imageurl.split("-")[0]
        try:
            # Entries older than 145 on the website are in .jpg format.
            if int(foxnum) > 145:
                extension = ".png"
            # And number 24 randomly truncates its name.
            elif int(foxnum) == 24:
                imageurl = "24"
                extension = ".jpg"
            else:
                extension = ".jpg"
        except ValueError:
            extension = ".jpg"
        imageurl = "http://stupidfox.net/art/" + imageurl + extension
        # For some reason, many of the page links on the website have duplicate dashes...
        imageurl = imageurl.replace("--", "-")
        em = discord.Embed(title='Random stupidfox! :fox:',
                           color=728077,
                           url=foxurl)
        em.set_image(url=imageurl)
        em.set_footer(
            text="Courtesy of Stupidfox.net. © Emily Chan",
            icon_url="https://scontent.fsnc1-1.fna.fbcdn.net/v/t1.0-9/14225402_10154540054369791_5558995243858647155_n.png?oh=2ea815515d0d1c7c3e4bbc561ff22f0e&oe=5A01CAD1"
        )
        await interaction.followup.send("<" + imageurl + ">", embed=em)
    else:
        # StupidFox is likely down if this command fails.
        await interaction.followup.send("Yip! I can't find a URL! I'm a stupid fox. :fox:")