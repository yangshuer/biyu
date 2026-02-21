from typing import List, Optional
from sqlalchemy import BigInteger, DECIMAL, ForeignKeyConstraint, Index, Integer, JSON, String, Text, text
from sqlalchemy.dialects.mysql import ENUM, VARCHAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import decimal

class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('username', 'email', unique=True),
        {'comment': '存储平台用户基本信息'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='用户唯一标识')
    email: Mapped[str] = mapped_column(String(50, 'utf8mb4_unicode_ci'), comment='用户邮箱，用于登陆')
    account_balance: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2), server_default=text("'0.00'"), comment='货币余额')
    password: Mapped[str] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='密码(加密存储)')
    username: Mapped[str] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='用户昵称')

    books: Mapped[List['Books']] = relationship('Books', back_populates='user')


class Books(Base):
    __tablename__ = 'books'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='books_ibfk_1'),
        Index('user_id', 'user_id'),
        {'comment': '作品核心元数据表'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='书籍唯一标识')
    user_id: Mapped[int] = mapped_column(BigInteger, comment='所属用户ID')
    title: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='作品名称')
    tags: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='分类标签（逗号分隔）')
    summary: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='作品简介')
    surface_plot: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='作品封面图url')
    space_setting: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='空间维度设定')
    time_setting: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='时间线设定')
    count_word_num: Mapped[Optional[int]] = mapped_column(Integer, comment='总字数')
    stats: Mapped[Optional[str]] = mapped_column(ENUM('创作中', '已中断', '已完结'), server_default='创作中', comment='作品状态')

    user: Mapped['Users'] = relationship('Users', back_populates='books')
    characters: Mapped[List['Characters']] = relationship('Characters', back_populates='book')
    locations: Mapped[List['Locations']] = relationship('Locations', back_populates='book')
    volumes: Mapped[List['Volumes']] = relationship('Volumes', back_populates='book')
    relationships: Mapped[List['Relationships']] = relationship('Relationships', back_populates='book')
    videos: Mapped[List['Videos']] = relationship('Videos', back_populates='book')


class Characters(Base):
    __tablename__ = 'characters'
    __table_args__ = (
        ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE', name='characters_ibfk_1'),
        Index('book_id', 'book_id'),
        {'comment': '角色详细设定档案'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='角色唯一标识')
    book_id: Mapped[int] = mapped_column(BigInteger, comment='所属作品ID')
    name: Mapped[Optional[str]] = mapped_column(String(100, 'utf8mb4_unicode_ci'), comment='角色全名')
    gender: Mapped[Optional[str]] = mapped_column(ENUM('男', '女', '其他'), comment='生理性别')
    personality: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='性格特征描述')
    background: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='背景故事')
    age: Mapped[Optional[int]] = mapped_column(Integer, comment='生理年龄')
    occupation: Mapped[Optional[str]] = mapped_column(String(100, 'utf8mb4_unicode_ci'), comment='主要职业')
    appearance: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='面部特征描述')
    physique: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='体型特征描述')
    face_image: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='角色面容图路径，用于视频生成人物一致性')
    race: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='角色种族')

    book: Mapped['Books'] = relationship('Books', back_populates='characters')
    relationships: Mapped[List['Relationships']] = relationship('Relationships', foreign_keys='[Relationships.source_id]', back_populates='source')
    relationships_: Mapped[List['Relationships']] = relationship('Relationships', foreign_keys='[Relationships.target_id]', back_populates='target')
    plots: Mapped[List['Plots']] = relationship('Plots', back_populates='protagonist')


class Locations(Base):
    __tablename__ = 'locations'
    __table_args__ = (
        ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE', name='locations_ibfk_1'),
        Index('book_id', 'book_id'),
        {'comment': '空间坐标及场景设定表'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='地点唯一标识')
    book_id: Mapped[int] = mapped_column(BigInteger, comment='所属作品ID')
    description: Mapped[str] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='空间环境描述')
    image: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='场景示意图路径')
    space_name: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='场景地点名')
    space_use: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='场景用途')

    book: Mapped['Books'] = relationship('Books', back_populates='locations')
    plots: Mapped[List['Plots']] = relationship('Plots', back_populates='location')


class Volumes(Base):
    __tablename__ = 'volumes'
    __table_args__ = (
        ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE', name='volumes_ibfk_1'),
        Index('book_id', 'book_id'),
        {'comment': '作品卷章结构表'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='分卷唯一标识')
    book_id: Mapped[int] = mapped_column(BigInteger, comment='所属作品ID')
    title: Mapped[str] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='分卷名称')
    phase: Mapped[Optional[str]] = mapped_column(ENUM('起始阶段', '发展阶段', '高潮阶段', '结局阶段'), comment='故事阶段')
    overview: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='分卷内容概要')
    num: Mapped[Optional[int]] = mapped_column(Integer, comment='卷序号')

    book: Mapped['Books'] = relationship('Books', back_populates='volumes')
    chapters: Mapped[List['Chapters']] = relationship('Chapters', back_populates='volume')


class Chapters(Base):
    __tablename__ = 'chapters'
    __table_args__ = (
        ForeignKeyConstraint(['volume_id'], ['volumes.id'], ondelete='CASCADE', name='chapters_ibfk_1'),
        Index('volume_id', 'volume_id'),
        {'comment': '章节详细配置表'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment='章节唯一标识')
    volume_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属分卷ID')
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False, comment='章节序号')
    title: Mapped[str] = mapped_column(String(255, 'utf8mb4_unicode_ci'), nullable=False, comment='章节标题')
    overview: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='章节内容提要')
    plots_text: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='章节情节的文本描述。')
    ai_creation: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='ai生成内容')
    human_creation: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='人类创作内容')
    status: Mapped[Optional[int]] = mapped_column(Integer, server_default='0', comment='章节状态：0-待创作，1-ai创作完成，2-人工编辑完成')
    ai_plots_text: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='ai情节设计')

    volume: Mapped['Volumes'] = relationship('Volumes', back_populates='chapters')
    plots: Mapped[List['Plots']] = relationship('Plots', back_populates='chapter')
    videos: Mapped[List['Videos']] = relationship('Videos', back_populates='chapter')


class Relationships(Base):
    __tablename__ = 'relationships'
    __table_args__ = (
        ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE', name='relationships_ibfk_1'),
        ForeignKeyConstraint(['source_id'], ['characters.id'], ondelete='CASCADE', name='relationships_ibfk_2'),
        ForeignKeyConstraint(['target_id'], ['characters.id'], ondelete='CASCADE', name='relationships_ibfk_3'),
        Index('book_id', 'book_id'),
        Index('source_id', 'source_id'),
        Index('target_id', 'target_id'),
        {'comment': '角色关系拓扑表'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='关系唯一标识')
    book_id: Mapped[int] = mapped_column(BigInteger, comment='所属作品ID')
    source_id: Mapped[int] = mapped_column(BigInteger, comment='关系发起方')
    target_id: Mapped[int] = mapped_column(BigInteger, comment='关系接收方')
    relationship_type: Mapped[str] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='关系类型')

    book: Mapped['Books'] = relationship('Books', back_populates='relationships')
    source: Mapped['Characters'] = relationship('Characters', foreign_keys=[source_id], back_populates='relationships')
    target: Mapped['Characters'] = relationship('Characters', foreign_keys=[target_id], back_populates='relationships_')


class Plots(Base):
    __tablename__ = 'plots'
    __table_args__ = (
        ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='CASCADE', name='plots_ibfk_1'),
        ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='SET NULL', name='plots_ibfk_2'),
        ForeignKeyConstraint(['protagonist_id'], ['characters.id'], ondelete='SET NULL', name='plots_ibfk_3'),
        Index('chapter_id', 'chapter_id'),
        Index('location_id', 'location_id'),
        Index('protagonist_id', 'protagonist_id'),
        {'comment': '情节单元（视频镜头脚本）详细记录表'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment='情节唯一标识')
    chapter_id: Mapped[int] = mapped_column(BigInteger, comment='所属章节ID')
    time_description: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='时间')
    event: Mapped[str] = mapped_column(Text(collation='utf8mb4_unicode_ci'), comment='事件内容')
    location_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='发生场景ID')
    protagonist_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='核心角色ID')
    num: Mapped[Optional[int]] = mapped_column(Integer, comment='情节序号')

    chapter: Mapped['Chapters'] = relationship('Chapters', back_populates='plots')
    location: Mapped[Optional['Locations']] = relationship('Locations', back_populates='plots')
    protagonist: Mapped[Optional['Characters']] = relationship('Characters', back_populates='plots')
    shots: Mapped[List['Shots']] = relationship('Shots', back_populates='plot')


class PlotSupportingRoles(Base):
    __tablename__ = 'plot_supporting_roles'
    __table_args__ = (
        ForeignKeyConstraint(['plotid'], ['plots.id'], ondelete='CASCADE', name='plot_supporting_roles_ibfk_1'),
        ForeignKeyConstraint(['bookid'], ['books.id'], ondelete='CASCADE', name='plot_supporting_roles_ibfk_2'),
        ForeignKeyConstraint(['characterid'], ['characters.id'], ondelete='CASCADE', name='plot_supporting_roles_ibfk_3'),
        Index('plotid', 'plotid'),
        Index('bookid', 'bookid'),
        Index('characterid', 'characterid'),
        {'comment': '情节配角表'}
    )

    plotid: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='情节ID')
    bookid: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='书籍id')
    characterid: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='角色ID')


class Videos(Base):
    __tablename__ = 'videos'
    __table_args__ = (
        ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE', name='videos_ibfk_1'),
        ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='SET NULL', name='videos_ibfk_2'),
        Index('book_id', 'book_id'),
        Index('chapter_id', 'chapter_id'),
        {'comment': '衍生视频素材表'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='视频唯一标识')
    book_id: Mapped[int] = mapped_column(BigInteger, comment='关联作品ID')
    chapter_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='对应章节ID')

    book: Mapped['Books'] = relationship('Books', back_populates='videos')
    chapter: Mapped[Optional['Chapters']] = relationship('Chapters', back_populates='videos')
    shots: Mapped[List['Shots']] = relationship('Shots', back_populates='video')


class Shots(Base):
    __tablename__ = 'shots'
    __table_args__ = (
        ForeignKeyConstraint(['plot_id'], ['plots.id'], ondelete='SET NULL', name='shots_ibfk_2'),
        ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE', name='shots_ibfk_1'),
        Index('plot_id', 'plot_id'),
        Index('video_id', 'video_id'),
        {'comment': '视频分镜头明细表'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='镜头唯一标识')
    video_id: Mapped[int] = mapped_column(BigInteger, comment='所属视频ID')
    plot_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='对应情节ID')

    plot: Mapped[Optional['Plots']] = relationship('Plots', back_populates='shots')
    video: Mapped['Videos'] = relationship('Videos', back_populates='shots')

class ApiKey(Base):
    __tablename__ = 'api_key'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT', onupdate='RESTRICT', name='user'),
        Index('user', 'user_id'),
        {'comment': 'API密钥管理表'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment='API密钥唯一标识')
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='用户id')
    base_url: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='支持的OpenAI模式API的baseurl的id')
    api_key: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='对应base API的key')
    status: Mapped[Optional[int]] = mapped_column(Integer, comment='应用状态：1-启用，0-弃用')
    scene: Mapped[Optional[int]] = mapped_column(Integer, comment='场景：0-chat、1-ontline、2-Creation')
    model_code: Mapped[Optional[str]] = mapped_column(String(255, 'utf8mb4_unicode_ci'), comment='模型代码')

    user: Mapped[Optional['Users']] = relationship('Users')