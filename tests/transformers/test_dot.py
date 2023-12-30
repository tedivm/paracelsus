from paracelsus.transformers.dot import Dot


def test_mermaid(metaclass):
    mermaid = Dot(metaclass=metaclass)
    graph_string = str(mermaid)

    assert '<tr><td colspan="3" bgcolor="lightblue"><b>users</b></td></tr>' in graph_string
    assert '<tr><td colspan="3" bgcolor="lightblue"><b>posts</b></td></tr>' in graph_string
    assert '<tr><td colspan="3" bgcolor="lightblue"><b>comments</b></td></tr>' in graph_string

    assert "users -- posts  [arrowhead=crow, arrowtail=none, dir=both, label=author];" in graph_string
    assert "posts -- comments  [arrowhead=crow, arrowtail=none, dir=both, label=post];" in graph_string
    assert "users -- comments  [arrowhead=crow, arrowtail=none, dir=both, label=author];" in graph_string

    assert '<tr><td align="left">CHAR(32)</td><td align="left">author</td><td>Foreign Key</td></tr>' in graph_string
    assert '<tr><td align="left">CHAR(32)</td><td align="left">post</td><td>Foreign Key</td></tr>' in graph_string
    assert '<tr><td align="left">DATETIME</td><td align="left">created</td><td></td></tr>' in graph_string
