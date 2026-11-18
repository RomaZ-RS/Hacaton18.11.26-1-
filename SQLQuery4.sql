use campus;

create table users 
(
    id int primary key identity(1,1),
    email nvarchar(50) unique not null,
    password nvarchar(30) not null default '123456', 
    surname nvarchar(50) not null,
    name nvarchar(50) not null,
    patronymic nvarchar(50),
    group_num nvarchar(10),
    role int not null 
);

create table events (
    id int primary key identity(1,1),
    code nvarchar(20) unique not null, 
    title nvarchar(200) not null,
    description nvarchar(max),
    category int, 
    starts_at datetime not null,
    place int, 
    capacity int not null,
    organizer_email nvarchar(100) not null,
    is_cancelled bit default 0 
);

create table registration 
(
    id int primary key identity(1,1),
    student_email nvarchar(100) not null,
    event_code nvarchar(20) not null,
    registered_at datetime default getdate(),
    constraint uq_registration unique (student_email, event_code),
    constraint fk_reg_user foreign key (student_email) references users(email),
    constraint fk_reg_event foreign key (event_code) references events(code)
);
